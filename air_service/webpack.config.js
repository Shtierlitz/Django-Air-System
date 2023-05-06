const path = require('path') // чтобы видел пути
const webpack = require('webpack'); // сам вебпак
const MiniCSSExtractPlugin = require('mini-css-extract-plugin')
const CssMinimizerPlugin = require('css-minimizer-webpack-plugin')
const TerserWenpackPlugin = require('terser-webpack-plugin')

// Сперва установить NodeJs https://nodejs.org/ #  node -v и npm -v чтобы проверить
// npm init -y в каталоге проекта
// npm install jquery --save - для установки jquery в систему
// npm install --save-dev mini-css-extract-plugin css-minimizer-webpack-plugin terser-webpack-plugin style-loader css-loader file-loader все нужные плагины

// npm run dev - разработка
// npm run build - продакшн

const isDev = process.env.NODE_ENV === 'development'
const isProd = !isDev
const optimization = () => {
    const config = {}
    if (isProd) {
        config.minimizer = [
            new CssMinimizerPlugin(),
            new TerserWenpackPlugin()
        ]
    }
    return config
}

module.exports = {
    entry: {
        main: './src/index.js',
        room: './src/chat_index.js',
        ticket: './src/ticket_index.js'
    }, // файлы откуда читает импорты
    output: {
        filename: '[name].boundle.js',
        path: path.resolve(__dirname, 'flights/static/flights/boundle/')
    }, // как и куда сохраняет
    optimization: optimization(), //оптимизация в спайке с dev и prod режимами
    plugins: [
        // ...
        new webpack.ProvidePlugin({
            $: 'jquery',
            jQuery: 'jquery',
        }), // привязывает jQuery к $
        new MiniCSSExtractPlugin({
            filename: 'styles1.css'
        }), // сожимает и создает новый css
        new MiniCSSExtractPlugin({
            filename: 'bootstrap.css'
        }) // сожимает и создает новый css
    ],
    module: {
        rules: [
            {
                test: /\.css$/,
                use: [
                    {
                        loader: MiniCSSExtractPlugin.loader,
                    },
                    'css-loader'
                ]
            },
            {
                test: /\.(ttf|woff|woff2|eot)$/,
                use: ['file-loader']
            }
        ]
    }
}