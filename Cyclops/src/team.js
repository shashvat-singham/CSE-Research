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
       
        
<span className="px-1"></span>
           <div className="font-sans font-bold text-2xl" ><center>Team </center></div>
           <div className="font-mono flex flex-row  justify-center items-center gap-8 text-bold border-2 bg-gray-200 col-span-1
                  border-gray-500 px-5 py-5  p-6 rounded-lg shadow-lg">

                <div className="font-mono flex flex-col items-center justify-center gap-2 font-bold border-2 bg-red-200 text-lg
                  border-red-200  p-5 rounded-lg shadow-lg ">
                    <a href="https://www.cse.iitk.ac.in/users/pkalita/">
                    <img src = {pk}/>
                    </a>
                    <div>
                    Pankaj Kumar Kalita
                    </div><div>
                    PhD student
                    </div>

                    </div>
               <div className="font-mono flex flex-col items-center justify-center gap-2 font-bold border-2 bg-red-200 text-lg
                  border-red-200  p-5 rounded-lg shadow-lg ">
                   <a href="https://www.cse.iitk.ac.in/users/sumitl/">
                   <img src = {sl} /> </a>
                   <div>
                    Sumit Lahiri
                    </div><div>
                    PhD student
                    </div>
                    </div>
               <div className="font-mono flex flex-col items-center justify-center gap-2 font-bold border-2 bg-red-200 text-lg
                  border-red-200  p-5 rounded-lg shadow-lg ">
                   <a href="https://www.cse.iitk.ac.in/users/subhajit/">
                   <img src = {sr} />
                   </a>
                   <div>
                    Dr. Subhajit Roy
                    </div><div>
                    Associate Professor
                    </div>
               </div>

           </div>        
         


    
</>
          )
        }
        
        
        }

export default about;





  