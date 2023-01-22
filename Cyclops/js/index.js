$(document).ready(function () {
    //Hide the loading spinner
    $("#pageloader").hide();

    //Generates the table
    $("#generate-table").click(function () {
        var grammar = $("#grammar").val();


        //removes any whitespace present
        var tmp_str = grammar.replace(/eps/g, '$');
        // grammar=grammar.replace(/\s/g,'');



        grammar = grammar.split("\n");



        //removes empty elements from array
        var grammar = grammar.filter(function (el) {
            return el != /\s/g;
        });

        //Check if all the values are filled
        if (grammar.length == 0) {
            alert("Fill the grammar");
            return;
        }



        var terms = [];
        var nonterms = [];

        for (var i = 0; i < grammar.length; i++) {
            var tmp2 = grammar[i].split("->");
            nonterms = nonterms.concat([tmp2[0]]);
        }

        var nonterm_uniq = []

        for (var i = 0; i < nonterms.length; i++) {
            if (nonterm_uniq.includes(nonterms[i]) == false) {
                nonterm_uniq = nonterm_uniq.concat([nonterms[i]]);
            }
        }

        nonterms = nonterm_uniq;
        nonterms = nonterms.map(e => String(e).trim());

        var uniq_str = [];
        tmp_str = tmp_str.replace(/;/g, ' ');
        tmp_str = tmp_str.replace(/->/g, ' ');
        tmp_str = tmp_str.replace(/\|/g, ' ');
        tmp_str = tmp_str.replace(/\$/g, '');
        tmp_str = tmp_str.split(/\s/g);
        tmp_str = tmp_str.filter(e => String(e).trim());
        for (var i = 0; i < tmp_str.length; i++) {
            if (nonterms.includes(tmp_str[i]) == false) {
                if (uniq_str.includes(tmp_str[i]) == false) {
                    uniq_str = uniq_str.concat(tmp_str[i]);
                }
            }
        }
        terms = uniq_str;

        //Numbering rules
        var table2 = "<table id=\"table2\" class=\"table table-responsive table-borderless table-striped table-dark overflow-auto\">";
        table2 = table2 + "<thead><tr><th>Number</th><th>Rules</th></tr></thead>";
        var n = 1;
        for (var i = 0; i < grammar.length; i++) {
            var t = grammar[i].split("|");
            table2 = table2 + "<tr>";
            table2 = table2 + "<td>" + n + "</td>" + "<td>" + t[0] + "</td>";
            table2 = table2 + "</tr>";
            n++;
            var t2 = t[0].split("->");
            for (var j = 1; j < t.length; j++) {
                table2 = table2 + "<tr>";
                table2 = table2 + "<td>" + n + "</td>" + "<td>" + t2[0] + "->" + t[j] + "</td>";
                table2 = table2 + "</tr>";
                n++;
            }
        }
        table2 = table2 + "</table>";

        //Table creation
        var table = "<table class=\"table table-responsive table-borderless table-striped table-dark overflow-auto\">";
        for (var i = 0; i < nonterms.length + 1; i++) {
            if (i == 0) {
                table = table + "<thead><tr><th><input type=\"hidden\" name=\"no_of_terms\" id=\"no_of_terms\" value=\"" + (terms.length + 2) + "\"><input type=\"hidden\" name=\"no_of_nonterms\" id=\"no_of_nonterms\" value=\"" + (nonterms.length + 1) + "\"><input type=\"hidden\" name=\"cell00\" value=\"" + (terms.length + 2) * (nonterms.length + 1) + "\"></th>";
                table = table + "<th>$<input type=\"hidden\" name=\"cell01\" id=\"cell01\" value=\"$\"><input type=\"hidden\" name=\"terms\" id=\"terms\" value=\"" + $("#terminals").val() + "\"><input type=\"hidden\" name=\"nonterms\" id=\"tnonerms\" value=\"" + $("#nonterminals").val() + "\"><input type=\"hidden\" name=\"grammar\" value=\"" + $("#grammar").val() + "\"></th>";

                for (var j = 0; j < terms.length; j++) {
                    var tmp = j + 2;
                    table = table + "<th>" + terms[j] + "<input type=\"hidden\" name=\"cell0" + tmp + "\" id=\"cell0" + tmp + "\" value=\"" + terms[j] + "\"></th>";
                }
                table = table + "</thead>";
            }
            else {
                table = table + "<tr>";
                for (var j = 0; j < terms.length + 2; j++) {
                    if (j == 0) {
                        table = table + "<td><b>" + nonterms[i - 1] + "<input type=\"hidden\" name=\"cell" + i + "" + j + "\" value=\"" + nonterms[i - 1] + "\"></td>";
                    }
                    else {
                        table = table + "<td><input name=\"cell" + i + j + "\" placeholder=0 value=0 required/></td>";
                    }

                }
                table = table + "</tr>";
            }
        }
        table = table + "<tr><td class=\"text-center\" colspan=\"" + terms.length + 2 + "\"><input type=\"submit\" name=\"submit-btn\" value=\"Submit\" class=\"btn btn-success\"></td></tr></table>";
        $("table").remove()
        $("#parse-table").append(table);
        $("table2").remove();
        $("#rule-numbers").append(table2);
    })
    $("#parse-table").submit(function (e) {
        $("#pageloader").show();
    });
});
