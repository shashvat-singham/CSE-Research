import React from 'react';
import {BrowserRouter} from "react-router-dom"
import MainRouter from "./MainRouter"
import TableData from './form';
function App() {
  return (
    <div className="App">
    <BrowserRouter>
        <MainRouter />
      {/* <TableData /> */}
    </BrowserRouter>
    </div>
     
     
  
  );
}

export default App;
