use egg::*;

define_language! {
    pub enum Math {
        "+" = Add([Id; 2]),
        "-" = Sub([Id; 2]),
        "*" = Mul([Id; 2]),
        "/" = Div([Id; 2]),
        "^" = Pow([Id; 2]),
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

fn rules() -> Vec<Rewrite<Math, ()>> {
    vec![
        // Addition simplifications
        rewrite!("add-comm"; "(+ ?a ?b)" => "(+ ?b ?a)"),
        rewrite!("add-assoc"; "(+ (+ ?a ?b) ?c)" => "(+ ?a (+ ?b ?c))"),
        rewrite!("add-zero"; "(+ ?a 0)" => "?a"),
        rewrite!("zero-add"; "(+ 0 ?a)" => "?a"),

        // Subtraction simplifications
        rewrite!("sub-zero"; "(- ?a 0)" => "?a"),
        rewrite!("sub-self"; "(- ?a ?a)" => "0"),

        // Multiplication simplifications
        rewrite!("mul-comm"; "(* ?a ?b)" => "(* ?b ?a)"),
        rewrite!("mul-assoc"; "(* (* ?a ?b) ?c)" => "(* ?a (* ?b ?c))"),
        rewrite!("mul-zero"; "(* ?a 0)" => "0"),
        rewrite!("zero-mul"; "(* 0 ?a)" => "0"),
        rewrite!("mul-one"; "(* ?a 1)" => "?a"),
        rewrite!("one-mul"; "(* 1 ?a)" => "?a"),

        // Division simplifications
        rewrite!("div-one"; "(/ ?a 1)" => "?a"),
        rewrite!("div-self"; "(/ ?a ?a)" => "1" if is_not_zero("?a")),

        // Powers
        rewrite!("pow-one"; "(^ ?a 1)" => "?a"),
        rewrite!("pow-zero"; "(^ ?a 0)" => "1" if is_not_zero("?a")),
        rewrite!("pow-two"; "(^ ?a 2)" => "(* ?a ?a)"),

        // Reciprocal identities
        rewrite!("csc-def"; "(csc ?x)" <=> "(/ 1 (sin ?x))"),
        rewrite!("sec-def"; "(sec ?x)" <=> "(/ 1 (cos ?x))"),
        rewrite!("cot-def"; "(cot ?x)" <=> "(/ 1 (tan ?x))"),

        // Quotient identities
        rewrite!("tan-quot"; "(tan ?x)" <=> "(/ (sin ?x) (cos ?x))"),
        rewrite!("cot-quot"; "(cot ?x)" <=> "(/ (cos ?x) (sin ?x))"),

        // Pythagorean identities
        rewrite!("pythagorean-1"; "(+ (^ (sin ?x) 2) (^ (cos ?x) 2))" <=> "1"),
        rewrite!("pythagorean-1-alt1"; "(+ (* (sin ?x) (sin ?x)) (* (cos ?x) (cos ?x)))" <=> "1"),
        rewrite!("pythagorean-1-sub1"; "(- 1 (^ (sin ?x) 2))" <=> "(^ (cos ?x) 2)"),
        rewrite!("pythagorean-1-sub2"; "(- 1 (^ (cos ?x) 2))" <=> "(^ (sin ?x) 2)"),
        
        rewrite!("pythagorean-2"; "(+ 1 (^ (tan ?x) 2))" <=> "(^ (sec ?x) 2)"),
        rewrite!("pythagorean-2-alt"; "(+ (^ (tan ?x) 2) 1)" <=> "(^ (sec ?x) 2)"),
        
        rewrite!("pythagorean-3"; "(+ 1 (^ (cot ?x) 2))" <=> "(^ (csc ?x) 2)"),
        rewrite!("pythagorean-3-alt"; "(+ (^ (cot ?x) 2) 1)" <=> "(^ (csc ?x) 2)"),
    ].concat()
}

fn is_not_zero(vars: &str) -> impl Fn(&mut egraph::EGraph<Math, ()>, Id, &Subst) -> bool {
    let vars: egg::Var = vars.parse().unwrap();
    move |egraph, _, subst| {
        !egraph[subst[vars]].nodes.iter().any(|n| matches!(n, Math::Num(0)))
    }
}

fn verify_identity(start: &str, target: &str) {
    let start_expr: RecExpr<Math> = start.parse().unwrap();
    let target_expr: RecExpr<Math> = target.parse().unwrap();

    let mut runner = Runner::default()
        .with_expr(&start_expr)
        .with_expr(&target_expr)
        .run(&rules());

    // Explanation requires `.with_explanations_enabled()` on the egraph.
    // Wait, by default explanation might not be enabled in old representations, let's enable it.
    
    let root1 = runner.roots[0];
    let root2 = runner.roots[1];

    if runner.egraph.find(root1) == runner.egraph.find(root2) {
        println!("The identity is valid!");
        let mut explanation = runner.egraph.explain_equivalence(&start_expr, &target_expr);
        let s = explanation.get_flat_string();
        println!("Steps to verify:");
        println!("{}", s);
    } else {
        println!("Could not verify the identity within the limit.");
    }
}

fn main() {
    let start = "(+ (^ (sin x) 2) (^ (cos x) 2))";
    let target = "1";
    println!("Verifying: {} = {}", start, target);
    verify_identity(start, target);
}
