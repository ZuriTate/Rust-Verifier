use egg::*;
use serde::Serialize;

// ---------------------------------------------------------------------------
//  Language definition
// ---------------------------------------------------------------------------
define_language! {
    pub enum Math {
        "+" = Add([Id; 2]),
        "-" = Sub([Id; 2]),
        "*" = Mul([Id; 2]),
        "/" = Div([Id; 2]),
        "^" = Pow([Id; 2]),
        "neg" = Neg(Id),
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

// ---------------------------------------------------------------------------
//  Condition helper
// ---------------------------------------------------------------------------
fn is_not_zero(v: &'static str) -> impl Fn(&mut EGraph<Math, ()>, Id, &Subst) -> bool {
    let var: Var = v.parse().unwrap();
    move |egraph, _, subst| {
        !egraph[subst[var]]
            .nodes
            .iter()
            .any(|n| matches!(n, Math::Num(0)))
    }
}

// ---------------------------------------------------------------------------
//  All rewrite rules
// ---------------------------------------------------------------------------
fn rules() -> Vec<Rewrite<Math, ()>> {
    let mut rs: Vec<Rewrite<Math, ()>> = vec![
        // ── Algebra ─────────────────────────────────────────────────
        rewrite!("add-comm"  ; "(+ ?a ?b)"           => "(+ ?b ?a)"),
        rewrite!("add-assoc" ; "(+ (+ ?a ?b) ?c)"    => "(+ ?a (+ ?b ?c))"),
        rewrite!("add-zero"  ; "(+ ?a 0)"            => "?a"),
        rewrite!("zero-add"  ; "(+ 0 ?a)"            => "?a"),

        rewrite!("sub-zero"  ; "(- ?a 0)"            => "?a"),
        rewrite!("sub-self"  ; "(- ?a ?a)"            => "0"),

        rewrite!("mul-comm"  ; "(* ?a ?b)"            => "(* ?b ?a)"),
        rewrite!("mul-assoc" ; "(* (* ?a ?b) ?c)"     => "(* ?a (* ?b ?c))"),
        rewrite!("mul-zero"  ; "(* ?a 0)"             => "0"),
        rewrite!("zero-mul"  ; "(* 0 ?a)"             => "0"),
        rewrite!("mul-one"   ; "(* ?a 1)"             => "?a"),
        rewrite!("one-mul"   ; "(* 1 ?a)"             => "?a"),

        rewrite!("div-one"   ; "(/ ?a 1)"             => "?a"),
        rewrite!("div-self"  ; "(/ ?a ?a)"            => "1" if is_not_zero("?a")),

        rewrite!("pow-one"   ; "(^ ?a 1)"             => "?a"),
        rewrite!("pow-zero"  ; "(^ ?a 0)"             => "1" if is_not_zero("?a")),
        rewrite!("one-pow"   ; "(^ 1 ?a)"             => "1"),
        rewrite!("pow-two"   ; "(^ ?a 2)"             => "(* ?a ?a)"),
        rewrite!("sq-to-pow" ; "(* ?a ?a)"            => "(^ ?a 2)"),

        rewrite!("dist-mul-add"  ; "(* ?a (+ ?b ?c))" => "(+ (* ?a ?b) (* ?a ?c))"),
        rewrite!("factor-mul-add"; "(+ (* ?a ?b) (* ?a ?c))" => "(* ?a (+ ?b ?c))"),

        rewrite!("neg-def"   ; "(neg ?a)"             => "(* -1 ?a)"),
        rewrite!("mul-neg-one"; "(* -1 ?a)"           => "(neg ?a)"),
        rewrite!("neg-neg"   ; "(neg (neg ?a))"       => "?a"),

        rewrite!("cancel-add-sub" ; "(- (+ ?a ?b) ?b)" => "?a"),
        rewrite!("cancel-add-sub2"; "(- (+ ?a ?b) ?a)" => "?b"),

        rewrite!("dist-mul-sub" ; "(* ?a (- ?b ?c))" => "(- (* ?a ?b) (* ?a ?c))"),
        rewrite!("factor-mul-sub"; "(- (* ?a ?b) (* ?a ?c))" => "(* ?a (- ?b ?c))"),

        rewrite!("div-mul"   ; "(/ (* ?a ?b) ?b)" => "?a" if is_not_zero("?b")),
        rewrite!("div-add"   ; "(+ (/ ?a ?c) (/ ?b ?c))" => "(/ (+ ?a ?b) ?c)"),
        rewrite!("mul-div"   ; "(* ?a (/ ?b ?c))" => "(/ (* ?a ?b) ?c)"),
        rewrite!("div-div"   ; "(/ (/ ?a ?b) ?c)" => "(/ ?a (* ?b ?c))"),
    ];

    // Polynomial Shortcuts
    rs.extend(rewrite!("foil" ; "(* (+ ?a ?b) (+ ?c ?d))" <=> "(+ (* ?a ?c) (+ (* ?a ?d) (+ (* ?b ?c) (* ?b ?d))))"));
    rs.extend(rewrite!("sq-add" ; "(^ (+ ?a ?b) 2)" <=> "(+ (^ ?a 2) (+ (* 2 (* ?a ?b)) (^ ?b 2)))"));
    rs.extend(rewrite!("sq-sub" ; "(^ (- ?a ?b) 2)" <=> "(+ (^ ?a 2) (- (^ ?b 2) (* 2 (* ?a ?b))))"));
    rs.extend(rewrite!("diff-sq"; "(* (+ ?a ?b) (- ?a ?b))" <=> "(- (^ ?a 2) (^ ?b 2))"));
    rs.extend(rewrite!("sub-as-neg"; "(- ?a ?b)" <=> "(+ ?a (neg ?b))"));

    // Advanced fraction rules for common denominators
    rs.push(rewrite!("div-scale" ; "(/ (* ?a ?c) (* ?b ?c))" => "(/ ?a ?b)" if is_not_zero("?c")));
    rs.extend(rewrite!("add-fracs" ; "(+ (/ ?a ?b) (/ ?c ?d))" <=> "(/ (+ (* ?a ?d) (* ?c ?b)) (* ?b ?d))" if is_not_zero("?b") if is_not_zero("?d")));
    rs.extend(rewrite!("mul-fracs" ; "(* (/ ?a ?b) (/ ?c ?d))" <=> "(/ (* ?a ?c) (* ?b ?d))"));
    rs.extend(rewrite!("recip-mul" ; "(/ 1 (* ?a ?b))" <=> "(* (/ 1 ?a) (/ 1 ?b))"));

    // ── Reciprocal identities ───────────────────────────────────────
    rs.extend(rewrite!("csc-def" ; "(csc ?x)" <=> "(/ 1 (sin ?x))"));
    rs.extend(rewrite!("sec-def" ; "(sec ?x)" <=> "(/ 1 (cos ?x))"));
    rs.extend(rewrite!("cot-def" ; "(cot ?x)" <=> "(/ 1 (tan ?x))"));

    // ── Quotient identities ─────────────────────────────────────────
    rs.extend(rewrite!("tan-quot" ; "(tan ?x)" <=> "(/ (sin ?x) (cos ?x))"));
    rs.extend(rewrite!("cot-quot" ; "(cot ?x)" <=> "(/ (cos ?x) (sin ?x))"));

    // ── Pythagorean identities ──────────────────────────────────────
    rs.push(rewrite!("pyth-1"     ; "(+ (^ (sin ?x) 2) (^ (cos ?x) 2))" => "1"));
    rs.push(rewrite!("pyth-1-alt" ; "(+ (* (sin ?x) (sin ?x)) (* (cos ?x) (cos ?x)))" => "1"));
    rs.extend(rewrite!("pyth-1-sub1" ; "(- 1 (^ (sin ?x) 2))" <=> "(^ (cos ?x) 2)"));
    rs.extend(rewrite!("pyth-1-sub2" ; "(- 1 (^ (cos ?x) 2))" <=> "(^ (sin ?x) 2)"));

    rs.extend(rewrite!("pyth-2"     ; "(+ 1 (^ (tan ?x) 2))" <=> "(^ (sec ?x) 2)"));
    rs.extend(rewrite!("pyth-2-alt" ; "(+ (^ (tan ?x) 2) 1)" <=> "(^ (sec ?x) 2)"));
    rs.extend(rewrite!("pyth-2-sub" ; "(- (^ (sec ?x) 2) 1)" <=> "(^ (tan ?x) 2)"));
    rs.push(rewrite!("pyth-2-diff"  ; "(- (^ (sec ?x) 2) (^ (tan ?x) 2))" => "1"));

    rs.extend(rewrite!("pyth-3"     ; "(+ 1 (^ (cot ?x) 2))" <=> "(^ (csc ?x) 2)"));
    rs.extend(rewrite!("pyth-3-alt" ; "(+ (^ (cot ?x) 2) 1)" <=> "(^ (csc ?x) 2)"));
    rs.extend(rewrite!("pyth-3-sub" ; "(- (^ (csc ?x) 2) 1)" <=> "(^ (cot ?x) 2)"));
    rs.push(rewrite!("pyth-3-diff"  ; "(- (^ (csc ?x) 2) (^ (cot ?x) 2))" => "1"));

    // ── Even / odd ──────────────────────────────────────────────────
    rs.extend(rewrite!("sin-neg" ; "(sin (neg ?x))" <=> "(neg (sin ?x))"));
    rs.extend(rewrite!("cos-neg" ; "(cos (neg ?x))" <=> "(cos ?x)"));
    rs.extend(rewrite!("tan-neg" ; "(tan (neg ?x))" <=> "(neg (tan ?x))"));

    // ── Double-angle ────────────────────────────────────────────────
    rs.extend(rewrite!("sin-double" ; "(sin (* 2 ?x))" <=> "(* 2 (* (sin ?x) (cos ?x)))"));
    rs.extend(rewrite!("cos-double" ; "(cos (* 2 ?x))" <=> "(- (* 2 (^ (cos ?x) 2)) 1)"));

    rs
}

// ---------------------------------------------------------------------------
//  Public verification API
// ---------------------------------------------------------------------------
#[derive(Serialize, Clone)]
pub struct VerifyResult {
    pub verified: bool,
    pub steps: Vec<String>,
    pub step_count: usize,
    pub error: Option<String>,
}

pub fn verify(lhs: &str, rhs: &str) -> VerifyResult {
    let lhs_expr: RecExpr<Math> = match lhs.parse() {
        Ok(e) => e,
        Err(e) => {
            return VerifyResult {
                verified: false,
                steps: vec![],
                step_count: 0,
                error: Some(format!("Failed to parse LHS: {}", e)),
            }
        }
    };
    let rhs_expr: RecExpr<Math> = match rhs.parse() {
        Ok(e) => e,
        Err(e) => {
            return VerifyResult {
                verified: false,
                steps: vec![],
                step_count: 0,
                error: Some(format!("Failed to parse RHS: {}", e)),
            }
        }
    };

    let mut runner = Runner::default()
        .with_explanations_enabled()
        .with_expr(&lhs_expr)
        .with_expr(&rhs_expr)
        .with_iter_limit(70)
        .with_node_limit(150_000)
        .run(&rules());

    let root_lhs = runner.roots[0];
    let root_rhs = runner.roots[1];

    if runner.egraph.find(root_lhs) == runner.egraph.find(root_rhs) {
        let mut explanation = runner.explain_equivalence(&lhs_expr, &rhs_expr);
        let flat = explanation.get_flat_string();
        let steps: Vec<String> = flat
            .split('\n')
            .filter(|s| !s.is_empty())
            .map(|s| s.trim().to_string())
            .collect();
        let step_count = steps.len();
        VerifyResult {
            verified: true,
            steps,
            step_count,
            error: None,
        }
    } else {
        VerifyResult {
            verified: false,
            steps: vec![],
            step_count: 0,
            error: Some("Could not verify identity within search limits.".into()),
        }
    }
}
