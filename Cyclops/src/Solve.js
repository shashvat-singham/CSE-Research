import React,{Component} from "react"
import {Navbar,Nav,NavDropdown,Carousel,Alert,Card,Container,Row,Col } from 'react-bootstrap';
import {Link} from "react-router-dom";
import pk from './images/pp.jpeg';
import sl from './images/sumit.jpeg';
import sr from './images/subhajit.png';
import styled from 'styled-components';
import Frame from 'react-frame-component';
var Latex = require('react-latex');


class about extends Component{
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
  <Navbar.Brand href="">CYCLOPS</Navbar.Brand>
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
       
         
{localStorage.getItem("key")?
        
         
         
        <Alert   variant="success" className="mt-2">
          <p>
          You are Signed In..Now you can enjoy cyclops.
          
          <a href="http://localhost/cyclops/solve"  rel="noreferrer"><button className="btn btn-dark" >Make Calculations</button></a>
          
          </p>
          
        </Alert>:<Alert variant="success" className="mt-2">
          <p>
          Sign In to Visit cyclops and make calculations.
          <button type="button" class="btn btn-secondary btn-lg" disabled>Make Calculations</button>
          </p>
          
          
        </Alert>
        }       
                     
             
         
         
              

    
</>
          )
        }
        
        
        }

export default about;





