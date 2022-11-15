const path = require('path')

module.exports = {
    mode: 'none',
    entry: [
        './static/js/index.js',
    ],
//    resolve: {
//        modules: [
//            path.join(__dirname, 'static'),
//            'node_modules',
//        ],
//    },
    output: {
        path: path.join(__dirname, 'static', 'js'),
        filename: 'bundle.js'
    },
}
