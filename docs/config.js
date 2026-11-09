// AI 판정 서버(Cloudflare Worker) 주소. 로컬에서 열면 wrangler dev(8787)를 쓴다.
window.GRADER_URL = /^(localhost|127\.0\.0\.1)$/.test(location.hostname)
  ? "http://localhost:8787"
  : "https://yomi-risk-grader.WORKERS_SUBDOMAIN.workers.dev";
