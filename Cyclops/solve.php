<?php
error_reporting(E_ERROR | E_PARSE);

session_start();

// Check if the user is logged in, if not then redirect him to login page
// if (!isset($_SESSION["loggedin"]) || $_SESSION["loggedin"] !== true) {
//     header("location: login.php");
//     exit;
// }
//Output to be displayed
$output = "Output..";



//The number of columns in the table it's value would be 2 greater than actual number of terminals in input(a column for $ andd a column for non terminal value)
$no_of_terms = 0;

//The number of rows in the table it's value would be 1 greater than actual number of non terminals in input(a row for non terminal value)
$no_of_nonterms = 0;

//Input provided by userS
$terms = "";
$nonterms = "";
$grammar = "";

//Username for this session
$username = $_SESSION["username"];
session_write_close();

//creation of a folder for user on first time of login
if (is_dir("inputs/" . $username));
else {
    mkdir("inputs/" . $username);
    $pyfile = fopen("inputs/" . $username . "__init__.py", "w");
    fwrite($pyfile, "");
    fclose($pyfile);
}

//filter for empty elements of an array
function empty_elements($arr)
{
    return $arr != "" and $arr != " ";
}



//When reques is made
if ($_SERVER['REQUEST_METHOD'] === 'POST' && !empty($_POST['no_of_terms']) && !empty($_POST['no_of_nonterms'])) {


    // $terms=$_POST['terms'];
    // $nonterms=$_POST['nonterms'];
    $grammar = $_POST['grammar'];


    $no_of_terms = $_POST['no_of_terms'];
    $no_of_nonterms = $_POST['no_of_nonterms'];




    // $grammar_arr= explode(";", preg_replace('/\s+/', '', $grammar));
    $grammar_arr = explode("\n", $grammar);


    $grammar_arr = array_filter($grammar_arr, "empty_elements");

    //replace eps->$ and id->; for parsing purposes
    $grammar_arr = str_replace("eps", "$", $grammar_arr);
    $grammar_arr = str_replace("id", ";", $grammar_arr);


    $tym = time();

    //the set of productions
    $rules = "[";
    $rules_arr = array();
    $num_rules = 0;




    //Maximum size of rules
    $size_rules = 0;
    $flg = 0;
    for ($i = 0; $i < count($grammar_arr); $i++) {
        $tmp = explode("->", $grammar_arr[$i]);
        if (count($tmp) == 1) {
            $output = "Error : Syntax of grammar is not correct";
            $flg = 1;
            break;
        }
        $productions = explode("|", $tmp[1]);
        for ($j = 0; $j < count($productions); $j++) {
            $tmp_a = explode(" ", $productions[$j]);
            $tmp_a = array_filter(array_map('trim', $tmp_a), "empty_elements");
            $max_len = count($tmp_a);
            if ($max_len > $size_rules) $size_rules = $max_len;
        }
        // $rule_lengths = array_map('strlen', $productions);
        // $max_len=max($rule_lengths);
        // if($max_len>$size_rules)$size_rules=$max_len;
    }


    $n = 0;
    if ($flg == 0) {
        for ($i = 0; $i < count($grammar_arr); $i++) {
            $tmp = explode("->", $grammar_arr[$i]);
            $nonterm = $tmp[0];
            $productions = explode("|", $tmp[1]);
            for ($j = 0; $j < count($productions); $j++) {
                $tmp2 = explode(" ", $productions[$j]);
                $tmp2 = array_filter(array_map('trim', $tmp2), "empty_elements");
                array_unshift($tmp2, $nonterm);
                $rules_arr[$n] = $tmp2;
                //We are repacing eps with $ and id with ; for counting purposes
                $tmp2 = str_replace("$", "eps", $tmp2);
                $tmp2 = str_replace(";", "id", $tmp2);
                $tmp3 = count($tmp2);


                $rules = $rules . '[\'' . (join("','", $tmp2)) . '\'';


                for ($k = 0; $k < $size_rules - $tmp3 + 1; $k++) {
                    array_unshift($tmp2, "eps");
                    $rules = $rules . ',\'eps\'';
                }

                $rules = $rules . "],";
                $num_rules++;
                $n++;
            }
        }
    }

    //removes the last , from rules string
    $rules = substr($rules, 0, -1);
    $rules = $rules . ']';


    $a = array();

    //The table to be added in input python file
    $parse_table = "[";


    for ($x = 1; $x < $no_of_nonterms; $x++) {
        $parse_table = $parse_table . "{'non_term':'" . $_POST['cell' . $x . "0"] . "',";
        for ($y = 1; $y < $no_of_terms; $y++) {
            // $tmp=explode("->", (preg_replace('/\s+/', '', $_POST['cell'.$x.$y])));
            // if(count($tmp)==1){
            //     $output="Error : Syntax of grammar is not correct in parse table";
            //     $flg=1;
            //     break;
            // }
            // $tmp2=(str_split(str_replace('id',';',str_replace(';','',(str_replace('eps','$',str_replace('->','',($tmp[1])))))),1));
            // array_unshift( $tmp2, $tmp[0]);
            // if(in_array($tmp2,$rules_arr,TRUE)){
            $parse_table = $parse_table . "'" . $_POST['cell0' . $y] . "':'" . ($_POST['cell' . $x . $y]) . "',";
            // }
            // else{
            //     $flg=1;
            //     $output="The productions in table are different from grammar".array_search($tmp2,$rules_arr,true);
            //     break;
            // }
        }
        if ($flg) break;
        $parse_table = substr($parse_table, 0, -1);
        $parse_table = $parse_table . "},";
    }
    $parse_table = substr($parse_table, 0, -1);
    $parse_table = $parse_table . "]";


    if ($flg == 0) {

        $fileName = "inputs/" . $username . "/" . $tym . ".py";

        $pyfile = fopen($fileName, "w");


        //A string which would be the input python file
        $pycode = "# from 'game_src/game/views' import * 
from collections import *
def specs():
    
    config = {
        'num_rules': " . $num_rules . ", #Number of rules
        'size_rules' : " . $size_rules . ", #Number of symbols in RHS
        'num_nonterms' : " . ((int)$_POST['no_of_nonterms'] - 1) . ", #Number of nonterms
        'expansion_constant' : 4, #Determines the max. number of parse actions to take while parsing
        'optimize' : False, # enable optimized mode
        'neg_egs' : True, # consider negative examples 
        'threshold' : 0.2  # number of unsat cores to break
    }
    
    return accept_strings,reject_strings,config

def reverse_grammar(original_grammar):
    max_len=len(original_grammar[0])
    for i in range(len(original_grammar)):
        count=0
        for j in range(max_len):
            if(original_grammar[i][j]=='eps'):
                count+=1
        if(count==0):
            continue
        tmp_list=count*[\"eps\"]
        new_grammar=[original_grammar[i][0]]+tmp_list+original_grammar[i][1:]
        original_grammar[i]=new_grammar
        original_grammar[i]=original_grammar[i][0:max_len]
    return original_grammar

def getError():
    return \"2nd rule of follow set A,b\"
    
def find_original_grammar(eps=True):
    # original_grammar contains list of rules. First element of list is the left nonterminal in each rule.
    original_grammar = " . $rules . "
    # return get_original_grammar()
    return reverse_grammar(original_grammar)
    
def get_parse_table(convert = False):
    parse_table = " . $parse_table . "
    return parse_table
    
def nums():
    original_grammar = find_original_grammar()
    num_vars = {'num_rules':len(original_grammar), 'size_rules':len(original_grammar[0])-1}
    return num_vars
    
accept_strings = [\"b\",\"a b b\"]
reject_strings = [\"b a\"]
    ";

        fwrite($pyfile, $pycode);
        fclose($pyfile);
        // $output = shell_exec("python2 generate_parsetable.py inputs/" . $username . "/" . $tym . ".py");
        $output="10,20,30,40,50,60,70,80";
        // if (strcmp($output,"0,0,0,0,0,0,0,0")==0){
        //     rename($fileName,str_replace(".py","",$fileName)."_correct.py");
        //     echo '<script type="text/javascript">
        //         alert("Correct");
        //         </script>';
        // }
        
    }
}
?>

<!DOCTYPE html>
<html lang="en">

<head>
    <title>cyclops</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="assets/css/bootstrap.min.css">
    <link rel="stylesheet" href="assets/css/index.css">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat&display=swap" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Open+Sans&display=swap" rel="stylesheet">
    <!-- Bootstrap -->
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>
    <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.6/js/bootstrap.min.js"></script>

    <!-- <link href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.6/css/bootstrap.min.css" rel="stylesheet" /> -->

</head>

<body>
    <nav class="navbar navbar-expand-md" style="background-color: black;">
        <div class="container-fluid">
            <div class="navbar-header text-primary">
                <h1 style="color:white;"><b>Cyclops</b></h1>
            </div>
            <ul class="nav navbar-nav">
            <li><button type="button" class="btn btn-primary m-2 " data-toggle="modal" data-target="#instuctions">Instructions</button>
                <li><a class="text-white"  href="reset.php" text-decoration =" None"><button type="button" class="btn btn-primary m-2 ">Reset</button></a></li>
                
                <li><a class="text-white" href="http://localhost:3000/"><button type="button" class="btn btn-danger m-2 ">Home</button></a></li>
                <div class="modal fade" id="instuctions">
                    <div class="modal-dialog">
                        <div class="modal-content">
                            <!-- Modal Header -->
                            <div class="modal-header">
                                <h4 class="modal-title">Instructions</h4>
                                <button type="button" class="close" data-dismiss="modal">&times;</button>
                            </div>
                            <!-- Modal body -->
                            <div class="modal-body">
                                <p>Enter semicolon seperated values in the specified areas of terminals,non-terminals and grammar.</p>
                                <p>The format of grammar should be S->S(S) i.e LHS and RHS should be sperated by a '->' block only, otherwise you would get a syntax error.All the blank spaces would be neglected</p>
                                <p>Then press generate parse table button for creation of parse table.</p>
                                <p>Fill the parse table and press submit button.</p>
                            </div>
                            <!-- Modal footer -->
                            <div class="modal-footer">
                                <button type="button" class="btn btn-danger" data-dismiss="modal">Close</button>
                            </div>
                        </div>
                    </div>
                </div>
            </ul>
        </div>
    </nav>
    <div class="container-fluid">
        <div class="row">
            <div class="left-half left-wrapper col-sm-3 col-md-6 col-lg-7 p-2 bg-secondary min-vh-100 text-center">
                <!-- <div class=" container-fluid card-deck bg-secondary text-white text-center mt-2 p-2 ">
                    <div class="card bg-dark h-100">
                        <div class="card-header" style="background-color: black;">
                            <h3>Terminals</h3>
                        </div>
                        <div class="card-body p-3 overflow-auto" id="terminals-card">
                            <div class="input-group mb-3">
                                <textarea id="terminals" placeholder="Semi-colon seperated terminals" name="terminals" class="w-100 h-100" rows="3"><?php echo $terms; ?></textarea>
                            </div>
                        </div>
                    </div>
                    <div class="card bg-dark h-100">
                        <div class="card-header" style="background-color: black;">
                            <h3>Non-Terminals</h3>
                        </div>
                        <div class="card-body p-3 overflow-auto" id="nonterminals-card">
                            <div class="input-group mb-3">
                                <textarea id="nonterminals" placeholder="Semi-colon seperated non-terminals" name="nonterminals" class="w-100 h-100" rows="3"><?php echo $nonterms; ?></textarea>
                            </div>
                        </div>
                    </div>
                    
                </div> -->
                <div class="container-fluid text-white mt-2 p-2">
                    <div class="card bg-dark h-100">
                        <div class="card-header" style="background-color: black;">
                            <h3><b>Grammar</b></h3>
                        </div>
                        <div class="card-body p-3 overflow-auto" id="grammar-card">
                            <div class="textarea-input input-group mb-3">
                                <textarea class="w-100 h-100" placeholder="Please input LL(1) grammar" name="grammar" rows="10" id="grammar"><?php echo $grammar; ?></textarea>
                            </div>
                        </div>
                    </div>
                </div>
            
                <div class="container-fluid">
                    <button id="generate-table" class="btn btn-primary m-3">Generate Parse Table </button>
                </div>

                <div class="textarea-input container-fluid card-deck bg-secondary text-white text-center mt-2 p-2 ">
                    <div class="card bg-dark h-100 col-sm-3 col-md-3 col-lg-3">
                        <div class="card-body p-3 overflow-auto" id="terminals-card">
                            <form id="rule-numbers" class="form-group" method="post" action="<?php echo $_SERVER['PHP_SELF']; ?>">
                                <?php
                                // Creation of table after a request is made and form is processed
                                if ($_SERVER['REQUEST_METHOD'] === 'POST' && !empty($_POST['no_of_terms']) && !empty($_POST['no_of_nonterms'])) {
                                    echo "<table id=\"table2\" class=\"table table-responsive table-borderless table-striped table-dark overflow-auto\">";
                                    echo "<thead><tr><th>Number</th><th>Rules</th></tr></thead>";
                                    // echo $rules;
                                    $tmp_rules = str_replace("[", "", $rules);
                                    $tmp_rules = str_replace("eps", "", $tmp_rules);
                                    $tmp_rules = str_replace("'", "", $tmp_rules);
                                    $tmp_rules = str_replace("],", "|", $tmp_rules);
                                    $tmp_rules = str_replace("]", "", $tmp_rules);
                                    $tmp_rules = str_replace(",,", "", $tmp_rules);
                                    $tmp_rules = str_replace(",", "->", $tmp_rules);
                                    $tmp_rules_arr = explode("|", $tmp_rules);
                                    for ($i = 1; $i < count($tmp_rules_arr) + 1; $i++) {
                                        $tmp4 = explode("->", $tmp_rules_arr[$i - 1]);
                                        $first = $tmp4[0];
                                        $second = "";
                                        for ($j = 1; $j < count($tmp4); $j++) {
                                            $second = $second . " " . $tmp4[$j];
                                        }
                                        if ($second == "") {
                                            $second = 'eps';
                                        }
                                        echo "<tr><td>" . $i . "</td><td>" . $first . "->" . $second . "</td></tr>";
                                    }
                                    echo "</table>";
                                }
                                ?>
                            </form>
                        </div>
                    </div>
                    <div class="card bg-dark h-100 col-sm-9 col-md-9 col-lg-9">
                        <div class="card-body p-3 overflow-auto" id="nonterminals-card">
                            <form id="parse-table" class="form-group" method="post" action="<?php echo $_SERVER['PHP_SELF']; ?>">
                                <?php
                                // Creation of table after a request is made and form is processed
                                if ($_SERVER['REQUEST_METHOD'] === 'POST' && !empty($_POST['no_of_terms']) && !empty($_POST['no_of_nonterms'])) {
                                    echo "<table class=\"table table-responsive table-borderless table-striped table-dark overflow-auto\">";
                                    for ($i = 0; $i < $no_of_nonterms; $i++) {
                                        if ($i == 0) {
                                            echo "<thead><tr><th><input type=\"hidden\" name=\"no_of_terms\" id=\"no_of_terms\" value=\"" . $no_of_terms . "\"><input type=\"hidden\" name=\"no_of_nonterms\" id=\"no_of_nonterms\" value=\"" . $no_of_nonterms . "\"><input type=\"hidden\" name=\"cell00\" value=\"" . ($no_of_terms) * ($no_of_nonterms) . "\">";
                                            echo "<input type=\"hidden\" name=\"terms\" id=\"terms\" value=\"" . $terms . "\"><input type=\"hidden\" name=\"nonterms\" id=\"tnonerms\" value=\"" . $nonterms . "\"><input type=\"hidden\" name=\"grammar\" value=\"" . $grammar . "\"></th>";
                                            for ($j = 1; $j < $no_of_terms; $j++) {
                                                echo "<th><input type=\"hidden\" name=\"cell0" . $j . "\" id=\"cell0" . $j . "\" value=\"" . $_POST['cell0' . $j] . "\">" . $_POST['cell0' . $j] . "</th>";
                                            }
                                            echo "</thead>";
                                        } else {
                                            echo "<tr>";
                                            for ($j = 0; $j < $no_of_terms; $j++) {
                                                if ($j == 0) {
                                                    echo "<td class=\"font-weight-bold\">" . $_POST['cell' . $i . $j] . "<input type=\"hidden\" name=\"cell" . $i . $j . "\" value=\"" . $_POST['cell' . $i . $j] . "\"></td>";
                                                } else {
                                                    echo "<td><input name=\"cell" . $i . $j . "\" value=\"" . $_POST['cell' . $i . $j] . "\" required /></td>";
                                                }
                                            }
                                            echo "</tr>";
                                        }
                                    }
                                    echo "<tr><td class=\"text-center\" colspan=\"" . $no_of_terms . "\"><input type=\"submit\" name=\"submit-btn\" value=\"Submit\" class=\"btn btn-success\"></td></tr></table>";
                                }
                                ?>
                            </form>
                        </div>
                    </div>
                </div>

            </div>
            <?php
            $output = trim($output);
            $output_arr = explode(",", $output);
            $color_arr = array("del");
            // echo $output_arr;
            for ($i = 0; $i <= 7; $i++) {
                if ($output_arr[$i] >= 0 && $output_arr[$i] < 10) {
                    $output_arr[$i] = "#FFFFB7";
                    array_push($color_arr, "black");
                } else if ($output_arr[$i] >= 10 && $output_arr[$i] < 20) {
                    $output_arr[$i] = "#FFF192";
                    array_push($color_arr, "black");
                } else if ($output_arr[$i] >= 20 && $output_arr[$i] < 30) {
                    $output_arr[$i] = "#FFEA61";
                    array_push($color_arr, "black");
                } else if ($output_arr[$i] >= 30 && $output_arr[$i] < 40) {
                    $output_arr[$i] = "#FFDD3C";
                    array_push($color_arr, "black");
                } else if ($output_arr[$i] >= 40 && $output_arr[$i] < 50) {
                    $output_arr[$i] = "#FFD400";
                    array_push($color_arr, "black");
                } else if ($output_arr[$i] >= 50 && $output_arr[$i] < 60) {
                    $output_arr[$i] = "#FFEE00";
                    array_push($color_arr, "black");
                } else if ($output_arr[$i] >= 60 && $output_arr[$i] < 70) {
                    $output_arr[$i] = "#FBB806";
                    array_push($color_arr, "black");
                } else if ($output_arr[$i] >= 70 && $output_arr[$i] < 80) {
                    $output_arr[$i] = "#F6830C";
                    array_push($color_arr, "white");
                } else if ($output_arr[$i] >= 80 && $output_arr[$i] < 90) {
                    $output_arr[$i] = "#F24D11";
                    array_push($color_arr, "white");
                } else {
                    $output_arr[$i] = "#ED1717";
                    array_push($color_arr, "white");
                }
            }
            ?>
            <div class="col-sm-3 col-md-6 col-lg-5 bg-dark min-vh-100 p-5">
                <div rows="35" id="output" placeholder="Output" class="w-100">
                    <!-- <div style="padding:5px" class="container-fluid text-center bg-secondary" id="feedbacks">
                        <form style="font-family:Open Sans" id="feedback" class="form-group" method="post" action="feedback.php">
                            <input type="hidden" name="fileName" value=<?php echo $fileName; ?>>
                            Was this output provided by the tool useful? <br>
                            <input type="radio" name="quality" value="good">Yes
                            <input type="radio" name="quality" value="bad"> No
                            <input type="submit" name="feedback-submit-btn" value="Submit" class="btn btn-sm btn-success feedback-submit">
                        </form>
                    </div> -->
                    <h3 class="sol-headers">First Set</h3>
                    <div class="accordion" id="accordionExample">
                        <div class="card">
                            <div style="padding:0.5rem;" class="card-header" id="headingOne">
                                <h2 style="background-color:<?php echo $output_arr[0] ?>" class="mb-0 sol-card-h2">
                                    <button style="color:<?php echo $color_arr[1] ?>" class="btn btn-link sol-card-btn" type="button" data-toggle="collapse" data-target="#collapseOne" aria-expanded="true" aria-controls="collapseOne">
                                        If \(X\) is a Terminal <b>&#x25BC</b>
                                    </button>
                                </h2>
                            </div>
                            <div id="collapseOne" class="collapse show" aria-labelledby="headingOne" data-parent="#accordionExample">
                                <div class="card-body sol-body">
                                    Then \(FIRST(X)=\{X\}\)
                                </div>
                            </div>
                            <div class="card">
                                <div style="padding:0.5rem;" class="card-header" id="headingTwo">
                                    <h2 style="background-color:<?php echo $output_arr[1] ?>" class="mb-0 sol-card-h2">
                                        <button style="color:<?php echo $color_arr[2] ?>" class="btn btn-link sol-card-btn collapsed" type="button" data-toggle="collapse" data-target="#collapseTwo" aria-expanded="false" aria-controls="collapseTwo">
                                            If \(X\) is a Nonterminal <b>&#x25BC</b>
                                        </button>
                                    </h2>
                                </div>
                                <div id="collapseTwo" class="collapse" aria-labelledby="headingTwo" data-parent="#accordionExample">
                                    <div class="card-body sol-body">
                                        If \(X\) is a Nonterminal And \(X \rightarrow Y_1Y_2...Y_k\) -s a production for some \(k\geq 1\) then place \(a\) in \(FIRST(X)\) if for some \(i,a\) is in the \(FIRST(Y_i)\) and \(\epsilon\) is in all of \(FIRST(Y_1),...,FIRST(Y_{i-1});\)
                                        that is \(Y_1...Y_{i-1} \implies^* \epsilon.\) Id \(\epsilon\) is in \(FIRST(Y_j)\) for all \(j=1,2,...,k\), then add \(\epsilon\) to \(FIRST(X)\). For example, everything in \(FIRST(Y_1)\) is surely in \(FIRST(X)\). If \(Y_1\) does not derive \(\epsilon\), then we add
                                        nothing more to \(FIRST(X)\), but if \(Y_1\implies^*\epsilon\) then we add \(FIRST(Y_2)\), and so on. </div>
                                </div>
                            </div>
                            <div class="card">
                                <div style="padding:0.5rem;" class="card-header" id="heading3">
                                    <h2 style="background-color:<?php echo $output_arr[2] ?>" class="mb-0 sol-card-h2">
                                        <button style="color:<?php echo $color_arr[3] ?>" class="btn btn-link sol-card-btn collapsed" type="button" data-toggle="collapse" data-target="#collapse3" aria-expanded="false" aria-controls="collapse3">
                                            If \(X\rightarrow \epsilon\) is a Production <b>&#x25BC</b>
                                        </button>
                                    </h2>
                                </div>
                                <div id="collapse3" class="collapse" aria-labelledby="heading3" data-parent="#accordionExample">
                                    <div class="card-body sol-body">
                                        Then add \(\epsilon\) to \(FIRST(X)\).
                                    </div>
                                </div>
                            </div>
                        </div>
                        <h3 class="sol-headers">Follow Set</h3>
                        <div class="accordion" id="accordionExample">
                            <div class="card">
                                <div style="padding:0.5rem;" class="card-header" id="heading4">
                                    <h2 style="background-color:<?php echo $output_arr[3] ?>" class="mb-0 sol-card-h2">
                                        <button style="color:<?php echo $color_arr[4] ?>" class="btn btn-link sol-card-btn collapsed" type="button" data-toggle="collapse" data-target="#collapse4" aria-expanded="false" aria-controls="collapse4">
                                            Place $ in \(FOLLOW(S)\) <b>&#x25BC</b>
                                        </button>
                                    </h2>
                                </div>
                                <div id="collapse4" class="collapse" aria-labelledby="headingTwo" data-parent="#accordionExample">
                                    <div class="card-body sol-body">
                                        Where \(S\) is the start symbol, and $ is the input right endmarker.
                                    </div>
                                </div>
                            </div>
                            <div class="card">
                                <div style="padding:0.5rem;" class="card-header" id="heading5">
                                    <h2 style="background-color:<?php echo $output_arr[4] ?>" class="mb-0 sol-card-h2">
                                        <button style="color:<?php echo $color_arr[5] ?>" class="btn btn-link sol-card-btn collapsed" type="button" data-toggle="collapse" data-target="#collapse5" aria-expanded="false" aria-controls="collapse5">
                                            If there is a production \(A\rightarrow \alpha B\beta\) <b>&#x25BC</b>
                                        </button>
                                    </h2>
                                </div>
                                <div id="collapse5" class="collapse" aria-labelledby="heading5" data-parent="#accordionExample">
                                    <div class="card-body sol-body">
                                        Then everything in \(FIRST(\beta)\) except \(\epsilon\) is in \(FOLLOW(B)\)
                                    </div>
                                </div>
                            </div>
                            <div class="card">
                                <div style="padding:0.5rem;" class="card-header" id="heading6">
                                    <h2 style="background-color:<?php echo $output_arr[5] ?>" class="mb-0 sol-card-h2">
                                        <button style="color:<?php echo $color_arr[6] ?>" class="btn btn-link sol-card-btn collapsed" type="button" data-toggle="collapse" data-target="#collapse6" aria-expanded="false" aria-controls="collapse6">
                                            If there is a production \(A\rightarrow \alpha B\) or \(A\rightarrow \alpha B \beta\) <b>&#x25BC</b>
                                        </button>
                                    </h2>
                                </div>
                                <div id="collapse6" class="collapse" aria-labelledby="heading6" data-parent="#accordionExample">
                                    <div class="card-body sol-body">
                                        Where \(FIRST(\beta)\) contains \(\epsilon\), then everything in \(FOLLOW(A)\) is in \(FOLLOW(B)\)
                                    </div>
                                </div>
                            </div>
                        </div>
                        <h3 class="sol-headers">Parse Table Constraints</h3>
                        <div class="accordion" id="accordionExample">
                            <div class="card">
                                <div style="padding:0.5rem;" class="card-header" id="heading7">
                                    <h2 style="background-color:<?php echo $output_arr[6] ?>" class="mb-0 sol-card-h2">
                                        <button style="color:<?php echo $color_arr[7] ?>" class="btn btn-link sol-card-btn collapsed" type="button" data-toggle="collapse" data-target="#collapse7" aria-expanded="false" aria-controls="collapse7">
                                            For each terminal \(a\) in \(FIRST(\alpha)\) <b>&#x25BC</b>
                                        </button>
                                    </h2>
                                </div>
                                <div id="collapse7" class="collapse" aria-labelledby="heading7" data-parent="#accordionExample">
                                    <div class="card-body sol-body">
                                        Add \(A\rightarrow \alpha\) to \([A,a]\)
                                    </div>
                                </div>
                            </div>
                            <div class="card">
                                <div style="padding:0.5rem;" class="card-header" id="heading8">
                                    <h2 style="background-color:<?php echo $output_arr[7] ?>" class="mb-0 sol-card-h2">
                                        <button style="color:<?php echo $color_arr[8] ?>" class="btn btn-link sol-card-btn collapsed" type="button" data-toggle="collapse" data-target="#collapse8" aria-expanded="false" aria-controls="collapse8">
                                            If \(\epsilon\) is in \(FIRST(\alpha)\) <b>&#x25BC</b>
                                        </button>
                                    </h2>
                                </div>
                                <div id="collapse8" class="collapse" aria-labelledby="heading8" data-parent="#accordionExample">
                                    <div class="card-body sol-body">
                                        Then for each terminal \(b\) in \(FOLLOW(A)\), add \(A\rightarrow\alpha\) to \(M[A,b]\). If \(\epsilon\) is in \(FIRST(\alpha)\) and $ is in \(FOLLOW(A)\), add \(A\rightarrow \alpha\) to \(M[A,$]\) as well.
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div id="pageloader" class="text-center text-info align-middle">
                <div class="spinner-border" role="status" style="width: 9rem; height: 9rem;">
                    <span class="sr-only">Loading...</span>
                </div>
                <p class="text-info h1">Loading</p>
            </div>
            <?php
                if (strcmp($output,"0,0,0,0,0,0,0,0")==0){
                    rename($fileName,str_replace(".py","",$fileName)."_correct.py");
                    echo '<script type="text/javascript">
                        alert("Correct");
                        </script>';
                }
            ?>
            <!-- js -->
            <script src="js/bootstrap.min.js"></script>
            <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>
            <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
            <script type="text/javascript" id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
            <script src="js/index.js"></script>
</body>

</html>