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
       <div>
        <span className="px-5"></span>
           {/* <div className="flex flex-col gap-2 font-sans justify-center text-bold border-2 col-span-1 bg-gray-100
                  border-gray-500 px-5 py-5  p-6 rounded-lg shadow-lg text-lg">
              <p> For any technical difficulties or bugs regarding this site please send a mail to <span className="font-mono bg-yellow-200">pkalita@cse.iitk.ac.in</span> and <span className="font-mono bg-yellow-200">subhajit@iitk.ac.in</span>.</p>
           </div> */}
            <span className="px-1"></span>
          <div className="flex flex-col gap-2 font-sans justify-center text-bold border-2 col-span-1 bg-gray-100
                  border-gray-500 px-5 py-5  p-6 rounded-lg shadow-lg text-lg">

              <h4 className="font-bold text-xl">Problem statement:</h4>
              <p >Your group was asked to create an LL(1) parser for a given grammar.
                  As you were busy, your group members finished the assignment and sent the solution to you for verification.
              Clever you---you decided to use <a href="http://jsmachines.sourceforge.net/machines/ll1.html" className="text-blue-600 font-bold"> LL(1) parser generator </a>  to check the solution.
              But, to your dismay the constructed parse table is wrong!
              </p><p>
              Now, you know that your group members are careful, they could have created <em><b> exactly one error </b></em>
              while following the steps to LL(1) parser creation.
              To be more precide, they made a mistake in exactly one constraint of <Link  className="text-blue-600 font-bold" to="./#firstSet">first set</Link>, <Link className="text-blue-600 font-bold" to="./#followSet">follow set </Link>
              and <Link className="text-blue-600 font-bold" to="./#parseTable">parse table</Link> construction---at that too on a single non-terminal/terminal/production.
              You are required to locate the bug.
               </p><p>
              For your assistance, we have provided a bot,
              <span className="text-blue-600 font-bold"> Cyclops </span> <sup><Link to="./#paper1" id="ref1">1</Link></sup>,
              that will help you debug the fault. Given a grammar and an incorrect parse table,
              it ranks the potential error and you may use it for directing your debugging effort.
              Like you, Cyclops does not have any idea of the error and hence, the actual fault may not appear at the top of the ranked list,
              or may not appear at all.
           </p><p>
              Your TA would have provided a passcode to access the site (and identify your group).
              You should attempt the Grammar/Tasks assigned to you (we have kept all tasks open, in case you want to explore other tasks too);
              however, only the tasks assigned to you will be graded.
           </p><p>
              We provide a possible sample solution that we expect from you:
              <span className="text-red-900 font-bold"> <Latex>The error was in the second constraint of First Set
              construction corresponding to the non-terminal '$A$'. The terminal '$b$' was present as the first symbol in the body of
              production  $A \rightarrow b\ A\ c$ , and hence, should have been included in the first-set of '$A$'.
              Adding '$b$' to $FIRST(A)$, adds $A \rightarrow b\ A\ c$ to the parse table corresponding to non-terminal '$A$' and
              lookahead '$b$'. This is the correct parse table.</Latex></span>
           </p><p>
              You must provide an honest feedback about if <span className="text-blue-600 font-bold"> Cyclops </span> helped you solve the problem and how (about 50 words).
              We will grade you on the quality of this feedback.
              Please be honest; both positive and negative feedback is equally important to us.
           </p><p className="font-bold">
              Important: We intend to use your (anonymized) feedback in future publications.
              We assume that you provide your consent for the same when you provide feedback.
              In case you are not comfortable with the same, please send a mail to <span className="font-mono bg-yellow-200">subhajit@iitk.ac.in</span> and <span className="font-mono bg-yellow-200">pkalita@cse.iitk.ac.in</span>.
            </p>
          </div>
        <span className="px-1"></span>
           <div className="font-mono flex flex-col justify-center gap-6 text-bold border-2 bg-gray-100 col-span-1
                  border-gray-500 px-5 py-5  p-6 rounded-lg shadow-lg text-lg">
            <h4 className="font-bold text-xl font-sans"><a id="firstSet">Constraints for parse table creation:</a></h4>
                <div className="font-mono flex flex-col justify-center gap-6 text-bold border-2 bg-red-200
                  border-red-200  p-5 rounded-lg shadow-lg">
                <div className="font-mono font-bold bg-yellow-200">First set constraints:</div>
                <ol className="list-decimal ">
                  <li> If <Latex> $X$ </Latex> is a  terminal symbol then <Latex> $FIRST(X) = &#123;X&#125;$.</Latex> </li>
                     <li>
                        If <Latex> $X$ </Latex> is a non terminal symbol and <Latex>$X \rightarrow Y_1, Y_2,\ldots Y_k $</Latex> is a production, then
                         <br></br> &nbsp;&nbsp;If for some <Latex>$i$, $a$ is in $FIRST(Y_i)$ and $\epsilon$ is in all of $FIRST(Y_j)$ (such that $j &lt; i$)</Latex> then
                         <br></br> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<Latex>$a$ is in $FIRST(X)$. </Latex>
                         <br></br> &nbsp;&nbsp;<Latex>If $\epsilon$ is in $FIRST(Y_1) \ldots FIRST(Y_k)$ then $\epsilon$ is in $FIRST(X)$.</Latex>
                    </li>
                   <li>If <Latex> $X \rightarrow \epsilon$ is a production then $\epsilon$ is in $FIRST(X)$.</Latex> </li>
                </ol>
                </div>

               <div className="font-mono flex flex-col justify-center gap-6 text-bold border-2 bg-red-200
                  border-red-200  p-5 rounded-lg shadow-lg">
                <div className="font-mono font-bold bg-yellow-200"><a id="followSet">Follow set constraints:</a></div>
                <ol className="list-decimal ">
                  <li>  <Latex>Place $&dollar;$ in $FOLLOW(S)$, where $S$ is the start symbol and $&dollar;$  is the input right endmarker</Latex>. </li>
                  <li> <Latex> If there is a production $A \rightarrow \alpha B \beta$, then everything in $FIRST(\beta)$ except $\epsilon$ is in $FOLLOW(B)$ </Latex>.</li>
                  <li><Latex> If there is a production $A \rightarrow \alpha B$, or a production $A \rightarrow \alpha B \beta$, where $FIRST(\beta)$ contains
                    $\epsilon$, then everything in $FOLLOW(A)$ is in $FOLLOW(B)$.</Latex></li>
                </ol>
                </div>

               <div className="font-mono flex flex-col justify-center gap-6 text-bold border-2 bg-red-200
                  border-red-200  p-5 rounded-lg shadow-lg">
                   <div className="font-mono font-bold bg-yellow-200"><a id="parseTable">Parse Table set constraints:</a></div>
                   <ol className="list-decimal ">
                       <li><Latex> For each terminal $a$ in $FIRST(\alpha)$, add $A \rightarrow \alpha$ to $M[A, a]$.</Latex></li>
                       <li> <Latex> If $\epsilon$ is in $FIRST(\alpha)$, then for each terminal $b$ in $FOLLOW(A)$,
                       add $A \rightarrow \alpha$ to $M[A, b]$.
                          If $\epsilon$ is in $FIRST(\alpha)$ and $&dollar;$ is in $FOLLOW(A)$ add $A \rightarrow \alpha$ to $M[A,$ $&dollar;$$]$ as well.
                       </Latex> </li>
                   </ol>
               </div>
           </div>
                <span className="px-1"></span>
           <br/><br/>
        <div>
        <span className="px-2.5"></span>
        <sup id="paper1" className="text-base" >&nbsp;&nbsp; 1. Dhruv Singal, Palak Agarwal, Saket Jhunjhunwala and Subhajit Roy.
            <a href="https://easychair.org/publications/paper/DtjZ" className="text-blue-600 font-bold">Parse Condition: Symbolic Encoding of LL(1) Parsing</a>.
            In LPAR-22. 22nd International Conference on Logic for Programming, Artificial &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Intelligence and Reasoning, Awassa, Ethiopia,
            16-21 November. 2018. <Link to="./#ref1" >↩</Link></sup>
            </div>
           <span className="px-2.5"></span>
        </div>   
         
 
        
         
         


    
</>
          )
        }
        
        
        }

export default about;





  