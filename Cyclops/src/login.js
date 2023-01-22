import React,{Component} from "react"
import {Navbar,Nav,NavDropdown} from 'react-bootstrap';
import fire from "./config/fire"
import {Link,} from "react-router-dom";



class login extends Component{
    constructor(props)
    {
        super(props)
        this.login=this.login.bind(this)
        
         
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
  
   login(e)
   {
     e.preventDefault()
     fire.auth().signInWithEmailAndPassword(this.state.email,this.state.password).then((u)=>{
     console.log(u)
     localStorage.setItem('key', u.user.uid)
     this.props.history.push('/');
   
    }).catch((error)=>{
       localStorage.removeItem('test')
       this.setState({error:"wrong combination"})
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
  <Navbar.Brand href="#home">Cyclops</Navbar.Brand>
  <Navbar.Toggle aria-controls="responsive-navbar-nav" />
  <Navbar.Collapse id="responsive-navbar-nav">
    <Nav className="mr-auto">
      <Nav.Link href="#features"><Link to="/">Home</Link></Nav.Link>
      <Nav.Link href="/problem">Problem </Nav.Link>
      <Nav.Link href="/solve">solve </Nav.Link>
      <Nav.Link href="/team">Team </Nav.Link>
      <Nav.Link href="/view">view </Nav.Link>
    </Nav>
    <Nav>
    <Nav.Link ><Link to="/regis">REGISTER</Link></Nav.Link>
    
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
<center><label  ><b>Login</b></label><br></br></center>

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
               
                
                <button className="btn btn-dark" onClick={this.login}>Sign In</button>  
                  
                
</form>
<hr/>
<p><br></br>Not having an account?  <Link to="/regis"> Register Now</Link></p>



</div>

</>
          )
          else
          return(
            <>
            <h1>please click below, you are already signed in</h1>
            <Link to="/">HOME</Link>
            </>
          )
        }
        
        
        }

export default login;





  