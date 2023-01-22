<?php
    if($_SERVER['REQUEST_METHOD'] === 'POST' && !empty($_POST['quality'])) {
        rename($_POST['fileName'],str_replace(".py","",$_POST['fileName']).'_'.$_POST['quality'].".py");
    }
    header("Location:solve");
    exit;
?>