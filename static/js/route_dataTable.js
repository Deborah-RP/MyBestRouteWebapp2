//Convert table data into 2D array
function convert_dt_to_arrays(tb_id, selected, searched){
    var table = $(tb_id).DataTable();
    var selector = {};
    //var ajax_data = table.ajax.json().data;
    var tb_data; 
    if (selected === true){
        //selector.selected = true;
        tb_data = table.rows(".selected").data();
    }
    else if (searched === true) {
        selector.search = 'applied';
        tb_data = table.rows(selector).data();
    }
    else {
        tb_data = table.rows().data();
    }

    var header = table.columns().header().context[0].aoColumns;
    var tb_arrays = [];
    var row = [];
    
    for (var idx = 0; idx < header.length; idx++){
        if (header[idx].data !== null) {
            var title = header[idx].title;
            row.push(title);
        }
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
    //print_obj(tb_params);
    var table = $(tb_params.tb_id).DataTable();
                
    //var row = aData[0];
    var rows = table.rows('.selected').data();
    var row = rows[0]

    for( var key in row) {
        var $form = $(tb_params.edit_modal_id)
        var query_str = "[name='" + key+"']";
        var form_field = $form.find(query_str) 
        
        //For repeated field, remove all the additonal fields
        if (form_field.length > 1){
            form_field.each(function( index ) {
                if (index > 0){
                    $(this).parent('div').remove(); 
                }
            });
        }
        if (row[key] !== null){
            var field_type = form_field.prop('type');
            //Set value for select field
            if (field_type === 'select-one') {
                //clear the previous selection
                form_field.val(null);
                
                //Handle the repeated select-one field
                if ($.isArray(row[key])){
                    var repeat_val = row[key];
                    //print_obj(repeat_val);
                    for (var idx=0; idx < repeat_val.length; idx++){
                        var current_val = repeat_val[idx];
                        sel_query = "option:contains('"+current_val+"')";
                        if (idx == 0){
                            form_field.find(sel_query).prop('selected', true);
                        }
                        else {
                            var new_field = create_new_field(form_field);
                            new_field.find(sel_query).prop('selected', true);
                            
                            console.log('creating new form_field at index: ' + idx);
                        }
                    }
                       
                }
            else {
                var sel_query = "option:contains('"+row[key]+"')";
                form_field.find(sel_query).prop('selected', true);                
            }
            }
            else {
                //Set value for select-multiple
              if (field_type === 'select-multiple') {
                  for (var idx=0; idx < row[key].length; idx++){
                      var each_value = row[key][idx];
                      var sel_query = "option:contains('"+each_value+"')";
                      //print_obj(form_field.find(sel_query));
                      form_field.find(sel_query).prop('selected', true);
                      form_field.bootstrapDualListbox('refresh');
                  }
              }
               else {
                    form_field.val(row[key]);    
                }
            }
        }
        else
            form_field.val("");
        }
        $(tb_params.edit_modal_id).modal('show');
    }

//Submit the delete data to the 
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


//Submit the activate data to the 
function activate_tb_rows(tb_params){
    
    var table = $(tb_params.tb_id).DataTable();
    var rows = table.rows('.selected').data();
    var act_data = []
    for (var idx = 0; idx < rows.length; idx++){
        act_data.push(rows[idx]);   
    }
    
    var ajax_data = {
        formType: 'async_activate', 
        act_data: JSON.stringify(act_data),        
    }
    json_async_submit(tb_params, ajax_data);
}


//Just the delete the data from the datatable without sending to server
function del_selected_row(tb_id){
    var table = $(tb_id).DataTable();
    table.row('.selected').remove().draw( false );
}

/*
Initialize the buttons for TableTools
*/
function init_tb_btn(tb_params){
    
    var btn_list = tb_params.tableTools.tb_buttons.split(",")
    var a_btns;
    
    if ($.inArray('create', btn_list) != -1){
        var create_btn = {
            sExtends: "text",
            sButtonText: "Create",
            fnClick: function(nButton, oConfig, oFlash) {
                $(tb_params.create_modal_id).modal('show');
                },
            };        
       a_btns = [create_btn];
    }
    else {
        a_btns = [];
    }
    
    if ($.inArray('edit', btn_list) != -1){
        var edit_btn = { 
            sExtends: "select_single", 
            sButtonText: "Edit",
            fnClick: function(nButton, oConfig, oFlash) {
                    //Get the current table
                    var tb_id = '#'+this.s.dt.sInstance;
                    var table = $(tb_id).DataTable();
                    var cur_tb_params = table.context[0].oInit.tb_params
                    edit_tb_row(cur_tb_params);
                },
            };        
        a_btns.push(edit_btn);   
    }
    
    if ($.inArray('edit_upload', btn_list) != -1){
        var edit_upload_btn = { 
            sExtends: "select_single", 
            sButtonText: "Modify",
            fnClick: function(nButton, oConfig, oFlash) {
                    //Get the current table
                    var tb_id = '#'+this.s.dt.sInstance;
                    var table = $(tb_id).DataTable();
                    var cur_tb_params = table.context[0].oInit.tb_params
                    $("#detele_table_id").val(tb_id);
                    edit_tb_row(cur_tb_params);
                },
            };        
        a_btns.push(edit_upload_btn);   
    }
        
    
    if ($.inArray('delete', btn_list) != -1){
        var del_btn = { 
            sExtends: "select", 
            sButtonText: "Delete",
            fnClick: function(nButton, oConfig, oFlash) {

                    var tb_id = '#'+this.s.dt.sInstance;
                    var table = $(tb_id).DataTable();
                    var cur_tb_params = table.context[0].oInit.tb_params

                    bootbox.confirm("Are you sure?", function(result){
                        if (result)
                            del_tb_rows(cur_tb_params);
                        else
                            return;
                    });
                },
            };        
        a_btns.push(del_btn);   
    }
    
    if ($.inArray('activate', btn_list) != -1){
        var act_btn = { 
            sExtends: "select", 
            sButtonText: "Activate",
            fnClick: function(nButton, oConfig, oFlash) {

                    var tb_id = '#'+this.s.dt.sInstance;
                    var table = $(tb_id).DataTable();
                    var cur_tb_params = table.context[0].oInit.tb_params

                    bootbox.confirm("Are you sure?", function(result){
                        if (result)
                            activate_tb_rows(cur_tb_params);
                        else
                            return;
                    });
                },
            };        
        a_btns.push(act_btn);   
    }    
    
    var filter_btn = {
        sExtends: "text",
        sButtonText: "Filter",
        fnClick: function(nButton, oConfig, oFlash) {
            console.log('click filter');
            var tb_id = '#'+this.s.dt.sInstance;
            var table = $(tb_id).DataTable();
            var cur_tb_params = table.context[0].oInit.tb_params
            cur_tb_params.scrollX = !cur_tb_params.scrollX;
             
            //$(tb_params.tb_id).removeAttr('no-footer'); 
            //$(tb_params.tb_id).removeAttr('DTTT_selectable');
            if (cur_tb_params.scrollX === false){
                for (var idx = 0; idx < cur_tb_params.tableTools.aButtons.length; idx++){
                    if ( cur_tb_params.tableTools.aButtons[idx].sButtonText === 'Filter'){
                        cur_tb_params.tableTools.aButtons[idx].sButtonText = 'Scroller';
                    }
                }
            }
            else {
                for (var idx = 0; idx < cur_tb_params.tableTools.aButtons.length; idx++){
                    if ( cur_tb_params.tableTools.aButtons[idx].sButtonText === 'Scroller'){
                        cur_tb_params.tableTools.aButtons[idx].sButtonText = 'Filter';
                    }
                }                
            }
            //print_obj(cur_tb_params);        
            init_dataTable(cur_tb_params);
        },
    }

    var csv_btn = {
        sExtends: "csv",
        sFileName: tb_params.dt_source +".csv",        
    };
    
    var pdf_btn = {
        sExtends: "pdf",
        sFileName: tb_params.dt_source +".pdf",        
    };    

    a_btns.push("select_all");   
    a_btns.push("select_none"); 
    a_btns.push(filter_btn);
    
    if ($.inArray('export', btn_list) != -1){
        
        var all_excel_btn = {
            sExtends: "text",
            sButtonText: "All to Excel",
            fnClick: function(nButton, oConfig, oFlash) {
                var tb_id = '#'+this.s.dt.sInstance;
                var table = $(tb_id).DataTable();
                var cur_tb_params = table.context[0].oInit.tb_params

                var tb_arrays = convert_dt_to_arrays(tb_id);
                export_array_to_excel(tb_arrays, cur_tb_params.dt_source)
            },
        };

        var selected_excel_btn = {
            sExtends: "text",
            sButtonText: "Selected to Excel",

            fnClick: function(nButton, oConfig, oFlash) {
                var tb_id = '#'+this.s.dt.sInstance;
                var table = $(tb_id).DataTable();
                var cur_tb_params = table.context[0].oInit.tb_params

                var tb_arrays = convert_dt_to_arrays(tb_id, true);
                export_array_to_excel(tb_arrays, cur_tb_params.dt_source)            
            },
        };   

        var searched_excel_btn = {
            sExtends: "text",
            sButtonText: "Searched to Excel",

            fnClick: function(nButton, oConfig, oFlash) {

                var tb_id = '#'+this.s.dt.sInstance;
                var table = $(tb_id).DataTable();
                var cur_tb_params = table.context[0].oInit.tb_params

                var tb_arrays = convert_dt_to_arrays(tb_id, false, true);
                export_array_to_excel(tb_arrays, cur_tb_params.dt_source)    
            },
        };      

        var export_btn = {
            "sExtends":    "collection",
            "sButtonText": "Export",
            "aButtons":    [ all_excel_btn, selected_excel_btn, searched_excel_btn, pdf_btn]
        };        
        a_btns.push(export_btn);   
    }    
    
    if ($.inArray('import', btn_list) != -1){
        var import_btn = {
            sExtends: "text",
            sButtonText: "Import",
            fnClick: function(nButton, oConfig, oFlash) {
                $(tb_params.dnd_id).show();
            },        
        };        
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
        tmp_obj.visible = true;
        tb_params.columns.push(tmp_obj);
        
        for (var idx = 0; idx < data.length; idx++){
            var col_def = data[idx];
            if (col_def.table_attr && (col_def.table_attr.indexOf("excluded") > -1)) {
                continue;   
            }
            tmp_obj = {};
            tmp_obj.title = col_def.label;
            tmp_obj.data = col_def.prop_name;
            tmp_obj.visible = true;
            if (col_def.table_attr && (col_def.table_attr.indexOf("hidden") > -1)) {
                tmp_obj.visible = false;
            }
            tb_params.columns.push(tmp_obj);
        }
        
        init_dataTable(tb_params);
    });
}

/*
Initialize the columns for dataTable for upload return
*/
function init_upload_tb_cols(tb_params){
    var tmp_obj = {};
    tmp_obj.title = "Failure Reason";
    tmp_obj.data = 'status_message';
    tb_params.columns.splice(1, 0, tmp_obj);

    //Go through the data source to make sure all the value is provided
    for (var row_idx =0; row_idx < tb_params.js_datasource.length; row_idx++){
        for (var col_idx = 0; col_idx < tb_params.columns.length; col_idx++){
            var col_data = tb_params.columns[col_idx].data;
            if (!(col_data in tb_params.js_datasource[row_idx])){
                tb_params.js_datasource[row_idx][col_data] = null;   
            }
            
        }
    }
    tb_params.scrollX = true;
    init_dataTable(tb_params);
}


/*
Initialize the dataTable
*/
function init_dataTable(tb_params){
    //print_obj(tb_params.tableTools.aButtons);
    var table, tb_init_params;
    if ($.fn.dataTable.isDataTable(tb_params.tb_id)) {
            $(tb_params.tb_id).DataTable().destroy();
            $(tb_params.tb_id).empty();
    }
    // Setup - add a text input to each footer cell
    tb_init_params = {};
    tb_init_params.columns = tb_params.columns;
    tb_init_params.order = tb_params.order;
    tb_init_params.dom = tb_params.dom;
    
    if (tb_params.scrollX === true){
        tb_init_params.scrollX = true
    }
    else {
        //Append footer as filter
        $(tb_params.tb_id).append('<tfoot><tr/></tfoot>');
        for (var idx = 0; idx < tb_params.columns.length; idx++){
            var col = tb_params.columns[idx];
            //if (col.visible === true)
                $(tb_params.tb_id+' tfoot tr').append('<th>'+col.title+'</th>');
            
    }
        
    }
    //tb_init_params.scrollX = true;
    //tb_init_params.sScrollX = "50%";
    tb_init_params.pageLength = 15;
    tb_init_params.language = {emptyTable: "Empty Table!"};
    tb_init_params.destroy = true;
    //tb_init_params.fixedHeader = {footer:true};
    
    if (tb_params.tableTools){
        tb_init_params.tableTools =  {
                    sSwfPath: "/swf/copy_csv_xls_pdf.swf",
                    sRowSelector: 'td:first-child',
                    sRowSelect: "multi",
                    aButtons: tb_params.tableTools.aButtons,
                };
    }

    if (tb_params.js_datasource){
        tb_init_params.data = tb_params.js_datasource;
    }
    else {
        tb_init_params.ajax = {
            url: tb_params.ajax,
            type: "POST",
            data: {
                formType: 'async_query_all_json',
                },
            dataSrc: function ( json ) {
                  return json.data;
                },
            };
    }
    //tb_init_params[tb_params.tb_id] = {};
    //tb_init_params[tb_params.tb_id].tb_params = JSON.parse(JSON.stringify(tb_params));
    //tb_init_params.tb_params = JSON.parse(JSON.stringify(tb_params));
    //tb_init_params.tb_params = tb_params;
    tb_init_params.tb_params =  $.extend(true, {}, tb_params);
    

    
    // empty in case the columns change
    
    table = $(tb_params.tb_id).DataTable(tb_init_params);
    //console.log("Creating " + tb_params.tb_id);
    //print_obj(table.context[0].oInit);
    
    if (!('scrollX' in tb_init_params)){
        $(tb_params.tb_id+' tfoot th').each( function () {
            var title = $(tb_params.tb_id+' thead th').eq( $(this).index() ).text();
            if (title != "Select") {
                $(this).html( '<input type="text" placeholder="Search '+title+'" />' );
            }
        } );

    // Apply the filter
    table.columns().every( function () {
        var column = this;
        var node = $(column.footer()).find('input');

        node.on( 'keyup change', function () {
            if (column.search() !== this.value){
            column
                .search( this.value )
                .draw();
                }
            });
        } );      
    }
    
    return table;
}

