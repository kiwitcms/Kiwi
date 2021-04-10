// JSON-RPC client inspired by
// https://stackoverflow.com/questions/8147211/jquery-jsonrpc-2-0-call-via-ajax-gets-correct-response-but-does-not-work
function jsonRPC(rpc_method, rpc_params, callback, is_sync) {
   // .filter() args are passed as dictionary but other args,
   // e.g. for .add_tag() are passed as a list of positional values
   if (!Array.isArray(rpc_params)) {
      rpc_params = [rpc_params]
   }

   $.ajax({
      url: '/json-rpc/',
      async: is_sync !== true,
      data: JSON.stringify({jsonrpc: '2.0',
                            method: rpc_method,
                            params: rpc_params,
                            id:"jsonrpc"}),  // id is needed !!
      // see "Request object" at https://www.jsonrpc.org/specification
      type:"POST",
      dataType:"json",
      contentType: "application/json",
      success: function (result) {
            if (result.error) {
                alert(result.error.message);
            } else {
                callback(result.result);
            }
      },
      error: function (err,status,thrown) {
             console.log("*** jsonRPC ERROR: " + err + " STATUS: " + status + " " + thrown );
      },
   });
}


// used by DataTables to convert a list of objects to a dict
// suitable for loading data into the table
function dataTableJsonRPC(rpc_method, rpc_params, callback, pre_process_data) {
    var internal_callback = function(data) {
        // used to collect additional information about columns via ForeignKeys
        if (pre_process_data !== undefined) {
            pre_process_data(data, callback);
        } else {
            callback({'data': data})
        }
    };

    jsonRPC(rpc_method, rpc_params, internal_callback);
}
