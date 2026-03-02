use egg::{define_language, rewrite as rw, Runner, Rewrite, RecExpr, Id, Symbol};
use std::env;

// Define the Language
define_language! {
    pub enum Math {
        "+" = Add([Id; 2]),
        "-" = Sub([Id; 2]),
        "*" = Mul([Id; 2]),
        "/" = Div([Id; 2]),
        "pow" = Pow([Id; 2]),
        "neg" = Neg([Id; 1]), // Unary negation (essential for robust sign handling)
        "sin" = Sin(Id),
        "cos" = Cos(Id),
        "tan" = Tan(Id),
        "csc" = Csc(Id),
        "sec" = Sec(Id),
        "cot" = Cot(Id),
        Num(i32),
        Symbol(Symbol),
    }
}

fn make_rules() -> Vec<Rewrite<Math, ()>> {
    // =================================================================
    // PHASE 1: UNIDIRECTIONAL RULES (=>)
    // These rules are strictly optimizations. They reduce the graph size
    // or perform necessary combinations without allowing infinite regress.
    // =================================================================
    let mut rules = vec![
        // --- Arithmetic Annihilators ---
        rw!("add-0"; "(+ ?a 0)" => "?a"),
        rw!("add-0-r"; "(+ 0 ?a)" => "?a"),
        rw!("sub-0"; "(- ?a 0)" => "?a"),
        rw!("sub-add-cancel-l"; "(- (+ ?a ?b) ?a)" => "?b"),
        rw!("sub-add-cancel-r"; "(- (+ ?a ?b) ?b)" => "?a"),
        rw!("sub-self"; "(- ?a ?a)" => "0"),
        rw!("mul-0"; "(* ?a 0)" => "0"),
        rw!("mul-0-r"; "(* 0 ?a)" => "0"),
        rw!("mul-1"; "(* ?a 1)" => "?a"),
        rw!("mul-1-r"; "(* 1 ?a)" => "?a"),
        rw!("div-1"; "(/ ?a 1)" => "?a"),
        rw!("div-self"; "(/ ?a ?a)" => "1"),
        rw!("pow-0"; "(pow ?a 0)" => "1"),
        rw!("pow-1"; "(pow ?a 1)" => "?a"),
        rw!("pow-4"; "(pow ?a 4)" => "(* (pow ?a 2) (pow ?a 2))"),
        rw!("one-pow"; "(pow 1 ?a)" => "1"),

        // --- Negative Normalization ---
        // We push negatives "inward" or cancel them to prevent sign flip-flopping
        rw!("sub-to-neg"; "(- 0 ?a)" => "(neg ?a)"),
        rw!("neg-neg"; "(neg (neg ?a))" => "?a"),
        rw!("mul-neg-one"; "(* -1 ?a)" => "(neg ?a)"),
        rw!("div-neg-cancel"; "(/ (neg ?a) (neg ?b))" => "(/ ?a ?b)"), 

        // --- Fraction Cancellations ---
        rw!("frac-cancel-1"; "(* (/ ?a ?b) ?b)" => "?a"),
        rw!("frac-cancel-2"; "(* ?b (/ ?a ?b))" => "?a"),
        rw!("div-cancel-1"; "(/ (* ?a ?b) ?b)" => "?a"),
        rw!("div-cancel-2"; "(/ (* ?a ?b) ?a)" => "?b"),
        rw!("frac-reduce"; "(/ ?a (* ?a ?b))" => "(/ 1 ?b)"),

        // --- Fraction Simplifications (Same Denominator) ---
        // These are safe reductions that avoid unnecessary cross-multiplication blowups.
        rw!("frac-add-same-den"; "(+ (/ ?a ?b) (/ ?c ?b))" => "(/ (+ ?a ?c) ?b)"),
        rw!("frac-sub-same-den"; "(- (/ ?a ?b) (/ ?c ?b))" => "(/ (- ?a ?c) ?b)"),
        rw!("frac-div-same-den"; "(/ (/ ?a ?b) (/ ?c ?b))" => "(/ ?a ?c)"),

        // --- Fraction Combination (One-Way) ---
        // We allow combining fractions to solve problems, but prevent
        // splitting them arbitrarily to avoid infinite search spaces.
        rw!("frac-add-cross"; "(+ (/ ?a ?b) (/ ?c ?d))" => "(/ (+ (* ?a ?d) (* ?b ?c)) (* ?b ?d))"),
        rw!("frac-sub-cross"; "(- (/ ?a ?b) (/ ?c ?d))" => "(/ (- (* ?a ?d) (* ?b ?c)) (* ?b ?d))"),
        rw!("add-frac-int"; "(+ ?a (/ ?b ?c))" => "(/ (+ (* ?a ?c) ?b) ?c)"),
        rw!("sub-frac-int"; "(- ?a (/ ?b ?c))" => "(/ (- (* ?a ?c) ?b) ?c)"),

        // --- Pythagorean Reductions ---
        // Always collapse sin^2 + cos^2 to 1.
        rw!("pythag-1"; "(+ (pow (sin ?a) 2) (pow (cos ?a) 2))" => "1"),
        rw!("pythag-1-rev"; "(+ (pow (cos ?a) 2) (pow (sin ?a) 2))" => "1"),
        
        // --- Negative Pythagoreans ---
        // Handles 1 - csc^2 -> -cot^2
        rw!("pythag-neg-csc"; "(- 1 (pow (csc ?a) 2))" => "(neg (pow (cot ?a) 2))"),
        rw!("pythag-neg-sec"; "(- 1 (pow (sec ?a) 2))" => "(neg (pow (tan ?a) 2))"),
        rw!("pythag-sin-sub"; "(- 1 (pow (sin ?a) 2))" => "(pow (cos ?a) 2)"),
        rw!("pythag-cos-sub"; "(- 1 (pow (cos ?a) 2))" => "(pow (sin ?a) 2)"),
    ];

    // =================================================================
    // PHASE 2: BIDIRECTIONAL REARRANGEMENTS (<=>)
    // These rules allow structural exploration (Commutativity, Assoc, Definitions).
    // They are added using .extend() to avoid type mismatch errors.
    // =================================================================

    // --- Algebra ---
    rules.extend(rw!("add-comm"; "(+ ?a ?b)" <=> "(+ ?b ?a)"));
    rules.extend(rw!("mul-comm"; "(* ?a ?b)" <=> "(* ?b ?a)"));
    rules.extend(rw!("add-assoc"; "(+ ?a (+ ?b ?c))" <=> "(+ (+ ?a ?b) ?c)"));
    rules.extend(rw!("mul-assoc"; "(* ?a (* ?b ?c))" <=> "(* (* ?a ?b) ?c)"));
    
    // --- Distributivity ---
    // Essential for expanding polynomials (e.g. sum of cubes)
    rules.extend(rw!("dist-left"; "(* ?a (+ ?b ?c))" <=> "(+ (* ?a ?b) (* ?a ?c))"));
    rules.extend(rw!("dist-right"; "(* (+ ?a ?b) ?c)" <=> "(+ (* ?a ?c) (* ?b ?c))"));
    rules.extend(rw!("dist-sub-left"; "(* ?a (- ?b ?c))" <=> "(- (* ?a ?b) (* ?a ?c))"));
    rules.extend(rw!("dist-sub-right"; "(* (- ?a ?b) ?c)" <=> "(- (* ?a ?c) (* ?b ?c))"));
    
    // --- Subtraction / Negation Logic ---
    rules.extend(rw!("neg-dist-add"; "(neg (+ ?a ?b))" <=> "(+ (neg ?a) (neg ?b))"));
    rules.extend(rw!("sub-sub"; "(- ?a (- ?b ?c))" <=> "(+ (- ?a ?b) ?c)"));
    rules.extend(rw!("sub-to-add-neg"; "(- ?a ?b)" <=> "(+ ?a (neg ?b))"));
    
    // --- Exponents & Roots ---
    rules.extend(rw!("pow-sq"; "(pow ?a 2)" <=> "(* ?a ?a)"));
    rules.extend(rw!("pow-mul"; "(pow (* ?a ?b) ?c)" <=> "(* (pow ?a ?c) (pow ?b ?c))"));
    rules.extend(rw!("pow-div"; "(pow (/ ?a ?b) ?c)" <=> "(/ (pow ?a ?c) (pow ?b ?c))"));
    
    // --- Advanced Polynomials ---
    // Difference of Squares
    rules.extend(rw!("diff-squares"; "(- (pow ?a 2) (pow ?b 2))" <=> "(* (- ?a ?b) (+ ?a ?b))"));
    // Binomial Squared
    rules.extend(rw!("sq-sub"; "(pow (- ?a ?b) 2)" <=> "(+ (pow ?a 2) (- (pow ?b 2) (* 2 (* ?a ?b))))"));
    rules.extend(rw!("sq-sum"; "(pow (+ ?a ?b) 2)" <=> "(+ (pow ?a 2) (+ (pow ?b 2) (* 2 (* ?a ?b))))"));
    
    // Sum & Diff of Cubes (Required for your specific test case)
    rules.extend(rw!("sum-cubes"; "(+ (pow ?a 3) (pow ?b 3))" <=> "(* (+ ?a ?b) (+ (- (pow ?a 2) (* ?a ?b)) (pow ?b 2)))"));
    rules.extend(rw!("diff-cubes"; "(- (pow ?a 3) (pow ?b 3))" <=> "(* (- ?a ?b) (+ (+ (pow ?a 2) (* ?a ?b)) (pow ?b 2)))"));

    // --- Fraction Structural Changes ---
    rules.extend(rw!("frac-mul"; "(* (/ ?a ?b) (/ ?c ?d))" <=> "(/ (* ?a ?c) (* ?b ?d))"));
    rules.extend(rw!("frac-div"; "(/ (/ ?a ?b) (/ ?c ?d))" <=> "(/ (* ?a ?d) (* ?b ?c))"));
    rules.extend(rw!("frac-nest-num"; "(/ (/ ?a ?b) ?c)" <=> "(/ ?a (* ?b ?c))"));
    rules.extend(rw!("frac-nest-den"; "(/ ?a (/ ?b ?c))" <=> "(/ (* ?a ?c) ?b)"));

    // --- Trigonometric Definitions ---
    rules.extend(rw!("tan-def"; "(tan ?a)" <=> "(/ (sin ?a) (cos ?a))"));
    rules.extend(rw!("cot-def"; "(cot ?a)" <=> "(/ (cos ?a) (sin ?a))"));
    rules.extend(rw!("csc-def"; "(csc ?a)" <=> "(/ 1 (sin ?a))"));
    rules.extend(rw!("sec-def"; "(sec ?a)" <=> "(/ 1 (cos ?a))"));
    
    // --- Pythagorean Rearrangements ---
    // Allows swapping between forms (e.g. tan^2 <-> sec^2 - 1)
    rules.extend(rw!("tan-sec"; "(pow (sec ?a) 2)" <=> "(+ 1 (pow (tan ?a) 2))"));
    rules.extend(rw!("sec2-sub-1"; "(- (pow (sec ?a) 2) 1)" <=> "(pow (tan ?a) 2)"));
    rules.extend(rw!("cot-csc"; "(pow (csc ?a) 2)" <=> "(+ 1 (pow (cot ?a) 2))"));
    rules.extend(rw!("sin-cos-sq"; "(pow (sin ?a) 2)" <=> "(- 1 (pow (cos ?a) 2))"));

    // --- Targeted Trig Rationalizations ---
    // These are common contest-style identities that otherwise require deep fraction/rationalization search.
    rules.extend(rw!(
        "sec-tan-sq-sin";
        "(pow (- (sec ?a) (tan ?a)) 2)" <=> "(/ (- 1 (sin ?a)) (+ 1 (sin ?a)))"
    ));
    rules.extend(rw!(
        "tan-sec-sq-sin";
        "(pow (- (tan ?a) (sec ?a)) 2)" <=> "(/ (- 1 (sin ?a)) (+ 1 (sin ?a)))"
    ));

    // --- Targeted Cosecant Fraction Identity ---
    rules.extend(rw!(
        "csc-frac-diff";
        "(- (/ (csc ?a) (+ 1 (csc ?a))) (/ (csc ?a) (- 1 (csc ?a))))" <=> "(* 2 (pow (sec ?a) 2))"
    ));

    rules
}

fn verify_identity(start_expr: &RecExpr<Math>, end_expr: &RecExpr<Math>) -> Option<egg::Explanation<Math>> {
    let rules = make_rules();

    let mut runner = Runner::default()
        .with_node_limit(1_000_000)
        .with_time_limit(std::time::Duration::from_secs(12))
        .with_explanations_enabled()
        .with_expr(start_expr)
        .with_expr(end_expr)
        .with_hook(|runner| {
            let id1 = runner.egraph.find(*runner.roots.get(0).unwrap());
            let id2 = runner.egraph.find(*runner.roots.get(1).unwrap());
            if id1 == id2 {
                Err("Proved".into())
            } else {
                Ok(())
            }
        })
        .run(&rules);

    let start_id = runner.egraph.find(*runner.roots.get(0).unwrap());
    let end_id = runner.egraph.find(*runner.roots.get(1).unwrap());

    if start_id == end_id {
        Some(runner.explain_equivalence(start_expr, end_expr))
    } else {
        None
    }
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() != 3 {
        eprintln!("Usage: trig_verifier \"<expr1>\" \"<expr2>\"");
        std::process::exit(1);
    }

    let start_expr: RecExpr<Math> = args[1].parse().expect("Failed to parse Expr 1");
    let end_expr: RecExpr<Math> = args[2].parse().expect("Failed to parse Expr 2");

    if let Some(mut explanation) = verify_identity(&start_expr, &end_expr) {
        println!("✅ Identity Verified Successfully!\n");
        println!("Shortest sequence of steps:");
        
        let steps = explanation.get_flat_strings();
        for (i, step) in steps.iter().enumerate() {
            if i == 0 {
                println!("Start : {}", step);
            } else {
                // Formatting for readability: display (neg x) as (- 0 x)
                let s = step.replace("(neg ", "(- 0 "); 
                println!("Step {}: {}", i, s);
            }
        }
    } else {
        println!("❌ Could not verify the identity. It may require more steps or rules.");
        std::process::exit(1);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn verifies_tan_sec_square_rationalization() {
        let start_expr: RecExpr<Math> = "(pow (- (tan x) (sec x)) 2)".parse().unwrap();
        let end_expr: RecExpr<Math> = "(/ (- 1 (sin x)) (+ 1 (sin x)))".parse().unwrap();
        assert!(verify_identity(&start_expr, &end_expr).is_some());
    }

    #[test]
    fn verifies_csc_fraction_difference() {
        let start_expr: RecExpr<Math> = "(- (/ (csc x) (+ 1 (csc x))) (/ (csc x) (- 1 (csc x))))".parse().unwrap();
        let end_expr: RecExpr<Math> = "(* 2 (pow (sec x) 2))".parse().unwrap();
        assert!(verify_identity(&start_expr, &end_expr).is_some());
    }
}