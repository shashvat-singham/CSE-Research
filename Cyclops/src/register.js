import React,{Component} from "react"
import {Navbar,Nav,NavDropdown} from 'react-bootstrap';
import fire from "./config/fire"
import {Link,} from "react-router-dom";



class register extends Component{
    constructor(props)
    {
        super(props)
        this.signup=this.signup.bind(this)
        
         
         this.handleChange=this.handleChange.bind(this)
        this.state ={
            email:"",
            password:"",
            user:{},
            error:""
            
        }
    }
    componentDidMount()
    {
      this.authListener();
    }
    authListener()
    {
      fire.auth().onAuthStateChanged((user)=>{
        if(user)
        {
         this.setState({user})
       }
        else this.setState({user:null})
      })
   }
  
     signup(e)
     {
      
         e.preventDefault()
         fire.auth().createUserWithEmailAndPassword(this.state.email,this.state.password).then((u)=>{
         console.log(u)
         if(window.confirm("Proceed to login"))
                this.props.history.push("/login")

                 }).catch((error)=>{
           this.setState({error:"email already taken or details wrong"})
           console.log(error)})
         this.setState({
             email:"",
             password:"",
             open1:true
              })
            
     }
     handleChange(e)
     {
       this.setState({error:""})
         this.setState({
             [e.target.name]:e.target.value
         })
     }
    
render()
{
  if(!localStorage.getItem("key"))
    return(
        <>
        
        
  <Navbar  collapseOnSelect expand="lg" bg="dark" variant="dark">
  <Navbar.Brand href="#home">CYCLOPS</Navbar.Brand>
  <Navbar.Toggle aria-controls="responsive-navbar-nav" />
  <Navbar.Collapse id="responsive-navbar-nav">
    <Nav className="mr-auto">
      <Nav.Link href="#"><Link to="/">Home</Link></Nav.Link>
      <Nav.Link href="/problem">Problem </Nav.Link>
      <Nav.Link href="/solve">solve </Nav.Link>
      <Nav.Link href="/team">Team </Nav.Link>
      <Nav.Link href="/view">view </Nav.Link>
    </Nav>
    <Nav>
    
    <Nav.Link ><Link to="/login">LOGIN</Link></Nav.Link>
    </Nav>
  </Navbar.Collapse>
</Navbar>
<div className="mt-5 mx-auto" style={{ 
  padding: "20px", 
  width: "400px",
  border: "2px solid",
  
  overflow: "auto"}}>
 
    <div
                    className="alert alert-danger w-50 mx-auto"
                    style={{ display: this.state.error ? "" : "none" }}
                >
                    {this.state.error}
                </div>
<form>
<div className="form-group">
<center><label  ><b>Register Here</b></label><br></br></center>
                <label className="text-dark">Email</label>
                <input
                type="email"
                id="email"
                name="email"
                className="form-control"
                onChange={this.handleChange}
                value={this.state.email}/>
                </div>
                <div className="form-group">
                <label className="text-dark">Password</label>
                 <input
                 name="password"
                type="password"
                className="form-control"
                id="password"
                onChange={this.handleChange}
                value={this.state.password}/>
                </div>
               
                
                  <button className="btn btn-dark" onClick={this.signup}>SIGN UP</button>  
                  
                  <br></br>        
</form>
<hr/>
<p> <br></br>Already have an account?  <Link to="/login"> Sign In</Link></p>



</div>

</>
          )
          else
          return(
            <>
            <h1>YOU CANNOT REGISTER AS YOU ARE ALREADY SIGNED IN</h1>
            <Link to="/">HOME</Link>
            </>
          )
        }
        
        
        }

export default register;





  