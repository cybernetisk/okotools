var webpack = require('webpack');

var production = process.env.NODE_ENV === 'production';

module.exports = {
  entry: './index.js',
  devtool: production ? 'source-map' : 'cheap-module-eval-source-map',
  output: {
    path: __dirname,
    filename: 'bundle.js'
  },
  module: {
    loaders: [
      {test: /\.css$/, loader: 'style!css'},
      {test: /\.scss$/, loader: 'style!css!sass'},
      {test: /\.js$/, exclude: /node_modules/, loaders: ['react-hot', 'babel-loader']}
    ]
  },
  plugins: [
    new webpack.ProvidePlugin({
      'fetch': 'imports?this=>global!exports?global.fetch!whatwg-fetch'
    }),
  ]
}
