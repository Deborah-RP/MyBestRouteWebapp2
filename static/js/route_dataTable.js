//Convert table data into 2D array
function convert_dt_to_arrays(tb_id){
    var table = $(tb_id).DataTable();
    //var ajax_data = table.ajax.json().data;
    var tb_data = table.rows().data();

    var header = table.columns().header().context[0].aoColumns;
    var tb_arrays = [];
    var row = [];
    
    for (var idx = 0; idx < header.length; idx++){
        if (header[idx].data !== null) {
            var title = header[idx].title;
            row.push(title);
        }convert_dt_to_arrays
    }

    tb_arrays.push(row);
            
    for (var row_idx = 0; row_idx < tb_data.length; row_idx++)
    {
        var rec = tb_data[row_idx];
        row = [];
        for (var col_idx = 0; col_idx < header.length; col_idx++)
        {
            var key = header[col_idx].data;
            if (key !==null) {
                var val = get_desc_obj(rec, key);
                row.push(val);
            }
        }
        tb_arrays.push(row);
    }
    //print_obj(tb_arrays);
    return tb_arrays;
}

/*
* Display database with the datasource and column definition
* tb_id: the html dataTable id
* tb_data: the data source for the data
* tb_header: the key and display text for the table header
* ROUTE_PLAN_HTML: map the key to the data source structure
*/
function display_dataTable(tb_id, tb_data, tb_header){
    
    var tb_col_def =[];
    var key, table;
    
    var excel_btn = {
        sExtends: "text",
        sButtonText: "Excel",
        fnClick: function(nButton, oConfig, oFlash) {
            var tb_arrays = convert_dt_to_arrays(tb_id);
            export_array_to_excel(tb_arrays, "download")
        },
    };
    
    var a_btns = [ excel_btn, "pdf", "copy", "print"];    
   
    var tmp_obj = {};
    tmp_obj.title = "Select";
    tmp_obj.data = null;
    tmp_obj.defaultContent = '';
    tmp_obj.orderable = false;
    tb_col_def.push(tmp_obj);
    

    
    //print_obj(tb_header);
    for (key in tb_header){
        if (key in ROUTE_PLAN_HTML){
            tmp_obj = {};
            tmp_obj.title = tb_header[key];
            tmp_obj.data = ROUTE_PLAN_HTML[key].full_key;
            tb_col_def.push(tmp_obj);
        }
    }
    
    if ($.fn.dataTable.isDataTable(tb_id)) {
        $(tb_id).DataTable().destroy();
        // empty in case the columns change
        $(tb_id).empty();
    }
    
    $(tb_id).DataTable({
        destroy: true,
        data: tb_data,
        columns: tb_col_def,
        paging: true,
        ordering: true,
        dom: '<"clear">flritTp',
        tableTools: {
            sSwfPath: "/swf/copy_csv_xls_pdf.swf",
            sRowSelector: 'td:first-child',
            sRowSelect: "multi",
            aButtons: a_btns,
        },
        language: {
            emptyTable: "Empty Table!"
        }
    });
    return true;
}

function edit_tb_row(tb_params){
    /*var oTT = TableTools.fnGetInstance(current_tb_id);
    var aData = oTT.fnGetSelectedData();*/
    
    var table = $(tb_params.tb_id).DataTable();
                
    //var row = aData[0];
    var rows = table.rows('.selected').data();
    var row = rows[0]

    for( var key in row) {
        var $form = $(tb_params.edit_modal_id)
        var query_str = "[name='" + key+"']";
        var form_field = $form.find(query_str)                    
        if (row[key] !== null){
            var field_type = form_field.prop('type');
            if (field_type === 'select-one') {
                var sel_query = "option:contains('"+row[key]+"')";
                form_field.find(sel_query).prop('selected', true);
            }
            else {
                form_field.val(row[key]);
            }
        }
        else
            form_field.val("");
        }
        $(tb_params.edit_modal_id).modal('show');
    }

function del_tb_rows(tb_params){
    
    var table = $(tb_params.tb_id).DataTable();
    var rows = table.rows('.selected').data();
    var del_data = []
    for (var idx = 0; idx < rows.length; idx++){
        del_data.push(rows[idx]);   
    }
    
    var ajax_data = {
        formType: 'async_delete', 
        del_data: JSON.stringify(del_data),        
    }
    
    json_async_submit(tb_params, ajax_data);
}

/*
Initialize the buttons for TableTools
*/
function init_tb_btn(tb_params){
    
    var create_btn = {
        sExtends: "text",
        sButtonText: "Create",
        fnClick: function(nButton, oConfig, oFlash) {
            $(tb_params.create_modal_id).modal('show');
            },
        };
        
    var edit_btn = { 
        sExtends: "select_single", 
        sButtonText: "Edit",
        fnClick: function(nButton, oConfig, oFlash) {
                edit_tb_row(tb_params);
            },
        };

    var del_btn = { 
        sExtends: "select", 
        sButtonText: "Delete",
        fnClick: function(nButton, oConfig, oFlash) {
                bootbox.confirm("Are you sure?", function(result){
                    if (result)
                        del_tb_rows(tb_params);
                    else
                        return;
                });
            },
        };
        
    var excel_btn = {
        sExtends: "text",
        sButtonText: "Excel",
        fnClick: function(nButton, oConfig, oFlash) {
            var tb_arrays = convert_dt_to_arrays(tb_params.tb_id);
            export_array_to_excel(tb_arrays, tb_params.dt_source)
        },
    };
    
    var csv_btn = {
        sExtends: "csv",
        sFileName: tb_params.dt_source +".csv",        
    };
    
    var pdf_btn = {
        sExtends: "pdf",
        sFileName: tb_params.dt_source +".pdf",        
    };    
    
    var import_btn = {
        sExtends: "text",
        sButtonText: "Import",
        fnClick: function(nButton, oConfig, oFlash) {
            $(tb_params.dnd_id).show();
        },        
    };
    
    var export_btn = {
        "sExtends":    "collection",
        "sButtonText": "Export",
        "aButtons":    [ excel_btn, pdf_btn, "copy", "print"]
    };
    
    var btn_list = tb_params.tableTools.tb_buttons.split(",")
    print_obj(btn_list)
    var a_btns;
    if ($.inArray('create', btn_list) != -1){
       a_btns = [create_btn];
    }
    else {
        a_btns = [];
    }
    if ($.inArray('edit', btn_list) != -1){
        a_btns.push(edit_btn);   
    }
    
    if ($.inArray('delete', btn_list) != -1){
        a_btns.push(del_btn);   
    }
    
    a_btns.push("select_all");   
    a_btns.push("select_all"); 
    
    if ($.inArray('export', btn_list) != -1){
        a_btns.push(export_btn);   
    }    
    
    if ($.inArray('import', btn_list) != -1){
        a_btns.push(import_btn);   
    }    

    return a_btns;
}

/*
Initialize the columns for dataTable
*/
function init_tb_cols(tb_params){
    /*var posting = $.post("/query_config_form/",
                         {formType: 'async_query_kind', 
                          kind_name : tb_params.dt_source}
                        );*/
    
    var posting = $.post(tb_params.ajax,
                         {formType: 'async_query_kind', 
                          kind_name : tb_params.dt_source}
                        );
    
    
    posting.done(function(data){
        tb_params.columns = [];
        var tmp_obj = {};
        tmp_obj.title = "Select";
        tmp_obj.data = null;
        tmp_obj.defaultContent = '';
        tmp_obj.orderable = false;
        tb_params.columns.push(tmp_obj);
        
        for (var idx = 0; idx < data.length; idx++){
            var col_def = data[idx];
            if (col_def.table_attr && (col_def.table_attr.indexOf("excluded") > -1)) {
                continue;   
            }
            tmp_obj = {};
            tmp_obj.title = col_def.label;
            tmp_obj.data = col_def.prop_name;
            if (col_def.table_attr && (col_def.table_attr.indexOf("hidden") > -1)) {
                tmp_obj.visible = false;
            }
            tb_params.columns.push(tmp_obj);
        }
        //print_obj(tb_params.columns);
        init_dataTable(tb_params);
    });
}

/*
Initialize the dataTable
*/
function init_dataTable(tb_params){
    //print_obj(tb_params.tableTools.aButtons);
    var table
    
    if (tb_params.tableTools){
        table = $(tb_params.tb_id).DataTable(
            {
                ajax: {
                    url: tb_params.ajax,
                    type: "POST",
                    data: {
                        formType: 'async_query_all_json',
                        },
                    dataSrc: function ( json ) {
                          return json.data;
                        },
                    },
                columns: tb_params.columns,
                order: tb_params.order,
                dom: tb_params.dom,
                scrollX: true,

                tableTools: {
                    sSwfPath: "/swf/copy_csv_xls_pdf.swf",
                    sRowSelector: 'td:first-child',
                    sRowSelect: "multi",
                    aButtons: tb_params.tableTools.aButtons,
                },
                language: {
                    emptyTable: "Empty Table!"
                }
            });
    }
    else{
       table = $(tb_params.tb_id).DataTable(
            {
                ajax: {
                    url: tb_params.ajax,
                    type: "POST",
                    data: {
                        formType: 'async_query_all_json',
                        },
                    dataSrc: function ( json ) {
                          return json.data;
                        },
                    },
                columns: tb_params.columns,
                order: tb_params.order,
                dom: tb_params.dom,
                scrollX: true,
                language: {
                    emptyTable: "Empty Table!"
                }
            });        
    }
    return table;
}

