import AllRequestPage from "./page/AllRequestPage";
import LandingPage from "./page/LandingPage";
import ReportPage from "./page/ReportPage";
import AdminLoginPage from "./page/AdminLoginPage";


export const mainRoute = [
    {
        path: "/",
        exact: true,
        component: LandingPage
    },
    {
        path: "/admin-login",
        exact: true,
        component: AdminLoginPage
    },
    {
        path: "/all-report",
        exact: true,
        component: AllRequestPage,
        protected: true
    },
    {
        path: "/report/:reportId",
        exact: true,
        component: ReportPage,
        protected: true
    },


]
