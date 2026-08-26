import { Switch, Route, Redirect } from "react-router-dom";
import { mainRoute } from "./routes";
import { isAdminAuthed } from "./api";


function App() {
  return (
    <>
      <Switch>
        {
          mainRoute.map((route, index) => {
            return (
              <Route
                key={index}
                path={route.path}
                exact={route.exact}
                render={(props) => {
                  // Route-level guard: protected admin pages require a valid
                  // admin session, otherwise redirect to the admin login.
                  if (route.protected && !isAdminAuthed()) {
                    return <Redirect to="/admin-login" />;
                  }
                  const Component = route.component;
                  return <Component {...props} />;
                }}
              />
            )
          })
        }
        <Redirect to='/' />
      </Switch>
    </>
  );
}

export default App;
