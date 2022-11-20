const path = require('path')

module.exports = {
    mode: 'none',
    entry: [
        './static/js/index.js'
    ],
    output: {
        path: path.join(__dirname, 'static', 'js'),
        filename: 'bundle.js'
    }
}
