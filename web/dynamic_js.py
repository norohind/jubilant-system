activity_table_html_template = """<!DOCTYPE HTML>
<html lang="en-US">
    <head>
        <meta charset="UTF-8">
        <script src="/js/json2htmltable.js"></script>
         <script type="text/javascript">
            window.addEventListener("load", () => {
                document.body.appendChild(buildHtmlTable({items}));  // build table

                var table = document.querySelector("body > table")
                var header = table.rows[0]

                for (var i = 0, cell; cell = header.cells[i]; i++){
                    if (cell.innerText.includes('{target_column_name}')){
                       var target_column_id = i;
                       break;
                    }
                }
                
                if (target_column_id == null) {  // don't to anything if no action_id in the table
                    return;
                }

                for (var i = 1, row; row = table.rows[i]; i++) {  // append to action_id filed onclick action
                   row.cells[target_column_id].innerHTML = '<td><a href="{link}">{original_value}</a></td>'.replace('{link}', '{target_new_url}' + table.rows[i].cells[target_column_id].innerText).replace('{original_value}', table.rows[i].cells[target_column_id].innerText);
                }
            })
        </script>
        <link type="text/css" rel="stylesheet" href="/js/table_styles.css">
    </head>
    <body>
    </body>
</html>"""