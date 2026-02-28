mod engine;

use serde::{Deserialize, Serialize};
use std::io::{self, Write};
use tiny_http::{Method, Response, Server};

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
//  CLI helpers
// ---------------------------------------------------------------------------
fn cli_verify(lhs: &str, rhs: &str) {
    let result = engine::verify(lhs, rhs);
    println!("\n Verifying:  {}  =  {}\n", lhs, rhs);
    if result.verified {
        println!("  ✓ Identity VERIFIED ({} steps)", result.step_count);
    } else {
        println!("  ✗ Could NOT verify.");
    }
}

fn demo_identities() -> Vec<(&'static str, &'static str, &'static str)> {
    vec![
        ("sin²x + cos²x = 1", "(+ (^ (sin x) 2) (^ (cos x) 2))", "1"),
        ("tan²x + 1 = sec²x", "(+ (^ (tan x) 2) 1)", "(^ (sec x) 2)"),
    ]
}

fn repl() {
    println!("\n[REPL Mode] Entering 'quit' to exit.");
    loop {
        print!("  LHS > ");
        io::stdout().flush().unwrap();
        let mut lhs = String::new();
        io::stdin().read_line(&mut lhs).unwrap();
        let lhs = lhs.trim();
        if lhs.is_empty() || lhs == "quit" { break; }
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
fn main() -> std::io::Result<()> {
    let args: Vec<String> = std::env::args().collect();
    
    if args.len() > 1 && args[1] == "serve" {
        let port = args.get(2).and_then(|p| p.parse().ok()).unwrap_or(8080);
        let server = Server::http(format!("127.0.0.1:{}", port)).unwrap();
        println!("🌐 Web Server running on http://localhost:{}", port);

        for mut request in server.incoming_requests() {
            let url = request.url().to_string();
            match (request.method(), url.as_str()) {
                (&Method::Post, "/api/verify") => {
                    let mut content = String::new();
                    let _ = request.as_reader().read_to_string(&mut content);
                    if let Ok(req_body) = serde_json::from_str::<VerifyRequest>(&content) {
                        let res = engine::verify(&req_body.lhs, &req_body.rhs);
                        let json = serde_json::to_string(&res).unwrap();
                        let response = Response::from_string(json)
                            .with_header(tiny_http::Header::from_bytes(&b"Content-Type"[..], &b"application/json"[..]).unwrap());
                        let _ = request.respond(response);
                    }
                }
                (&Method::Get, "/api/health") => {
                    let _ = request.respond(Response::from_string("ok"));
                }
                (&Method::Get, "/") | (&Method::Get, "/index.html") => {
                    let html = std::fs::read_to_string("static/index.html").unwrap_or_default();
                    let response = Response::from_string(html)
                        .with_header(tiny_http::Header::from_bytes(&b"Content-Type"[..], &b"text/html"[..]).unwrap());
                    let _ = request.respond(response);
                }
                _ => {
                    // Try serving static files (extremely basic)
                    let path = format!("static{}", url);
                    if let Ok(content) = std::fs::read(path) {
                        let response = Response::from_data(content);
                        let _ = request.respond(response);
                    } else {
                        let _ = request.respond(Response::from_string("Not Found").with_status_code(404));
                    }
                }
            }
        }
        Ok(())
    } else if args.len() == 3 {
        cli_verify(&args[1], &args[2]);
        Ok(())
    } else {
        demo_identities().into_iter().for_each(|(_, l, r)| cli_verify(l, r));
        repl();
        Ok(())
    }
}
