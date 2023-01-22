import React from "react";
import {Switch,Route} from "react-router-dom";


import Register from "./register"
import Home from "./Home"
import login from "./login"
import problem from "./problem";
import solve from "./Solve";
import team from "./team";
import view from "./view";
import table from "./table"


const MainRouter = () => (
    
    <div>
       
       
        <Switch>
        <Route exact path="/" component={Home} />
        <Route exact path="/regis" component={Register} />
        <Route exact path="/login" component={login} />
        <Route exact path="/problem" component={problem} />
        <Route exact path="/solve" component={solve} />
        <Route exact path="/team" component={team} />
        <Route exact path="/view" component={view} />
        <Route exact path="/table" component={table} />

        </Switch>
    </div>
);

export default MainRouter;
