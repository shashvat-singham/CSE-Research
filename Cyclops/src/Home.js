import React,{Component} from "react"
import {Navbar,Nav,NavDropdown,Carousel,Alert,Card,Container,Row,Col } from 'react-bootstrap';
import {Link} from "react-router-dom";
import "./home.css";
import table from "./table.jsx";
import pk from './images/pp.jpeg';
import sl from './images/sumit.jpeg';
import sr from './images/subhajit.png';
// import table from "./table.jsx";
class Home extends Component{
    constructor(props)
    {
        super(props)
        this.logout=this.logout.bind(this)
        this.state ={
            
        }
    }
    logout(e)
  {

     e.preventDefault()
    
      
       localStorage.removeItem('key')
      this.props.history.push('/')
     
      
      
     
 }
    
 
render()
{
    return(
        <>
       
        
  <Navbar  collapseOnSelect expand="lg" bg="dark" variant="dark">
  <Navbar.Brand href="">Fun with LL(1) </Navbar.Brand>
  <Navbar.Toggle aria-controls="responsive-navbar-nav" />
  <Navbar.Collapse id="responsive-navbar-nav">
  <Nav className="mr-auto">
      <Nav.Link href="/"><Link to="/">Home</Link></Nav.Link>
      <Nav.Link href="/problem">Problem </Nav.Link>
      <Nav.Link href="/solve">solve </Nav.Link>
      <Nav.Link href="/team">Team </Nav.Link>
      <Nav.Link href="/view">view </Nav.Link>
    </Nav>
    <Nav>
        {localStorage.getItem("key")?"":
        
         
    <Nav.Link ><Link to="/regis">REGISTER</Link></Nav.Link>}  
    {localStorage.getItem("key")?<Nav.Link href="#deets" onClick={this.logout}>LOGOUT</Nav.Link>:
        
         
        <Nav.Link ><Link to="/login">LOGIN</Link></Nav.Link>}                                                    
    </Nav>
  </Navbar.Collapse>
</Navbar>
 
{/* {localStorage.getItem("key")?
        
         
         
<Alert   variant="success" className="mt-2">
  <p>
  You are Signed In..Now you can enjoy cyclops.
  </p>
  
</Alert>:<Alert variant="success" className="mt-2">
  <p>
  Sign In to Visit cyclops and make calculations.
  </p>
  
</Alert>}        */}
         
         


         <div className="container1">
        <nav className="nav-bar">
          <h1 className="logo">CYCLOPS</h1>
          
        </nav>
        <div className="subCont">
          <h7 className="headline">
          <b>About</b>
          </h7>
          <p className="desc">
          Cyclops is a software system for teaching LL(1) parsing. Cyclops provides an interactive environment to learn LL(1) parsing.
           It uses formal method techniques (i.e., SMT solvers) to give feedback to the user in case of wrong entries of the LL(1) parse 
           table. Cyclops is built on the published work Parse Condition: Parsing{" "}
            <span style={{ color: "red" }}>Symbolic Encoding of LL(1) </span>
          </p>
          <h7 className="headline">
           <b>Publications</b>
          </h7>
          <p className="desc">
          Dhruv Singal, Palak Agarwal, Saket Jhunjhunwala and Subhajit Roy. Parse Condition: Symbolic Encoding of LL(1) Parsing. 
          Parsing{" "} 
            <span style={{ color: "red" }}><br></br>In LPAR-22. 22nd International Conference on Logic for Programming, Artificial Intelligence and Reasoning, Awassa, Ethiopia,
           16-21 November. 2018.  </span>
          </p>
        </div>
      </div>
      
      

      <footer className="footer">
        <div className="flinks">
        <h2>For any technical difficulties or bugs regarding this site please send a mail to pkalita@cse.iitk.ac.in and subhajit@iitk.ac.in.
        </h2>
        </div>
      </footer>



</>
          )


          
        }
        
        
        }
        

export default Home;





  