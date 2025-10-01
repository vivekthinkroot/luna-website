import { type RouteConfig, index, route } from "@react-router/dev/routes";

export default [
    index("routes/home.tsx"),
    route("pricing", "routes/pricing.tsx"),
    route("pdf", "routes/pdf.ts"),
    route("about", "routes/about.tsx"),
    route("login", "routes/login.tsx"),
    route("kundli", "routes/kundli.tsx"),
    route("kundli/redirect", "routes/kundli-redirect.tsx"),
    route("payment-test", "routes/payment-test.tsx"),
] satisfies RouteConfig;
