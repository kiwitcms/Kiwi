// JSON-RPC client inspired by
// https://stackoverflow.com/questions/8147211/jquery-jsonrpc-2-0-call-via-ajax-gets-correct-response-but-does-not-work
function jsonRPC(rpc_method, rpc_params, callback) {
   $.ajax({
      url: '/json-rpc/',
      data: JSON.stringify({jsonrpc: '2.0',
                            method: rpc_method,
                            params: [rpc_params],
                            id:"jsonrpc"}),  // id is needed !!
      // see "Request object" at https://www.jsonrpc.org/specification
      type:"POST",
      dataType:"json",
      contentType: "application/json",
      success: function (result) {
            callback(result.result);
      },
      error: function (err,status,thrown) {
             console.log("*** jsonRPC ERROR: " + err + " STATUS: " + status + " " + thrown );
      },
   });
}


// used by DataTables to convert a list of objects to a dict
// suitable for loading data into the table
function dataTableJsonRPC(rpc_method, rpc_params, callback) {
    var internal_callback = function(data) {
        callback({'data': data})
    };

    jsonRPC(rpc_method, rpc_params, internal_callback);
}
