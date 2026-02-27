mod engine;

use actix_cors::Cors;
use actix_files as fs;
use actix_web::{web, App, HttpResponse, HttpServer, Responder};
use serde::{Deserialize, Serialize};
use std::io::{self, Write};

// ---------------------------------------------------------------------------
//  API types
// ---------------------------------------------------------------------------
#[derive(Deserialize)]
struct VerifyRequest {
    lhs: String,
    rhs: String,
}

#[derive(Serialize)]
#[allow(dead_code)]
struct VerifyResponse {
    verified: bool,
    steps: Vec<String>,
    step_count: usize,
    error: Option<String>,
}

// ---------------------------------------------------------------------------
//  API handler
// ---------------------------------------------------------------------------
async fn verify_handler(body: web::Json<VerifyRequest>) -> impl Responder {
    let result = engine::verify(&body.lhs, &body.rhs);
    HttpResponse::Ok().json(result)
}

async fn health() -> impl Responder {
    HttpResponse::Ok().body("ok")
}

// ---------------------------------------------------------------------------
//  CLI helpers (kept for backwards-compat)
// ---------------------------------------------------------------------------
fn cli_verify(lhs: &str, rhs: &str) {
    let result = engine::verify(lhs, rhs);
    println!();
    println!("═══════════════════════════════════════════════════════");
    println!("  Verifying:  {}  =  {}", lhs, rhs);
    println!("═══════════════════════════════════════════════════════");
    if result.verified {
        println!("  ✓ Identity VERIFIED");
        println!();
        println!(
            "  Proof ({} step{}):",
            result.step_count,
            if result.step_count == 1 { "" } else { "s" }
        );
        println!("  ─────────────────────────────────────────────────");
        for (i, step) in result.steps.iter().enumerate() {
            println!("    {}. {}", i + 1, step);
        }
    } else {
        println!("  ✗ Could NOT verify the identity.");
        if let Some(e) = &result.error {
            println!("    Error: {}", e);
        }
    }
    println!();
}

fn demo_identities() -> Vec<(&'static str, &'static str, &'static str)> {
    vec![
        ("sin²x + cos²x = 1", "(+ (^ (sin x) 2) (^ (cos x) 2))", "1"),
        ("tan²x + 1 = sec²x", "(+ (^ (tan x) 2) 1)", "(^ (sec x) 2)"),
        ("cot²x + 1 = csc²x", "(+ (^ (cot x) 2) 1)", "(^ (csc x) 2)"),
        ("tanx = sinx / cosx", "(tan x)", "(/ (sin x) (cos x))"),
        ("cscx = 1 / sinx", "(csc x)", "(/ 1 (sin x))"),
        ("sec²x - tan²x = 1", "(- (^ (sec x) 2) (^ (tan x) 2))", "1"),
    ]
}

fn repl() {
    println!();
    println!("┌────────────────────────────────────────────────────────┐");
    println!("│         Trigonometric Identity Verifier                │");
    println!("│  S-expression syntax: (+ (^ (sin x) 2) (^ (cos x) 2))│");
    println!("│  Commands: demo, quit                                 │");
    println!("└────────────────────────────────────────────────────────┘");
    loop {
        println!();
        print!("  LHS > ");
        io::stdout().flush().unwrap();
        let mut lhs = String::new();
        io::stdin().read_line(&mut lhs).unwrap();
        let lhs = lhs.trim();
        if lhs.eq_ignore_ascii_case("quit") || lhs.eq_ignore_ascii_case("exit") {
            break;
        }
        if lhs.eq_ignore_ascii_case("demo") {
            for (name, l, r) in demo_identities() {
                println!("  ── {} ──", name);
                cli_verify(l, r);
            }
            continue;
        }
        print!("  RHS > ");
        io::stdout().flush().unwrap();
        let mut rhs = String::new();
        io::stdin().read_line(&mut rhs).unwrap();
        cli_verify(lhs, rhs.trim());
    }
}

// ---------------------------------------------------------------------------
//  Entry point
// ---------------------------------------------------------------------------
#[actix_web::main]
async fn main() -> std::io::Result<()> {
    // Process arguments: skip the program name and filter out any flags (starting with -)
    let pos_args: Vec<String> = std::env::args()
        .skip(1)
        .filter(|a| !a.starts_with('-'))
        .collect();

    match pos_args.as_slice() {
        // `cargo run -- serve` -> start web server
        [cmd, ..] if cmd == "serve" => {
            let port: u16 = pos_args.get(1)
                .and_then(|p| p.parse().ok())
                .unwrap_or(8080);

            println!("🌐 Starting Trig Verifier web server on http://localhost:{}", port);

            HttpServer::new(|| {
                let cors = Cors::permissive();
                App::new()
                    .wrap(cors)
                    .route("/api/verify", web::post().to(verify_handler))
                    .route("/api/health", web::get().to(health))
                    .service(fs::Files::new("/", "./static").index_file("index.html"))
            })
            .bind(("127.0.0.1", port))?
            .run()
            .await
        }
        // Exactly two positional args -> single verification
        [lhs, rhs] => {
            cli_verify(lhs, rhs);
            Ok(())
        }
        // No positional args -> demo + REPL
        [] => {
            println!("\n  Running demos...\n");
            for (name, l, r) in demo_identities() {
                println!("  ── {} ──", name);
                cli_verify(l, r);
            }
            repl();
            Ok(())
        }
        _ => {
            eprintln!("Usage:");
            eprintln!("  trig_verifier                          (interactive)");
            eprintln!("  trig_verifier \"<lhs>\" \"<rhs>\"          (verify one)");
            eprintln!("  trig_verifier serve [port]             (web server)");
            std::process::exit(1);
        }
    }
}
