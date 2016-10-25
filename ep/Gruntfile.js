/*global module:false*/
module.exports = function (grunt) {
    "use strict";

    // Project configuration.
    grunt.initConfig({
            targetdir: './../static/',
            pkg: '<json:package.json>',
            meta: {
                banner: '/*! <%= pkg.title || pkg.name %> - v<%= pkg.version %> - ' +
                '<%= grunt.template.today("yyyy-mm-dd") %>\n' +
                '<%= pkg.homepage ? "* " + pkg.homepage + "\n" : "" %>' +
                '* Copyright (c) <%= grunt.template.today("yyyy") %> <%= pkg.author.name %>;' +
                ' Licensed <%= _.pluck(pkg.licenses, "type").join(", ") %> */'
            },
            qunit: {
                files: ['test/js/**/*.html']
            },
            copy: {
                build: {
                    files: [
                        {
                            dest: "<%= targetdir%>/lib/",
                            src: ["**"],
                            cwd: 'bower_components/bootstrap/dist/',
                            expand: true
                        },
                        {dest: "<%= targetdir%>/lib/", src: ["**"], cwd: 'bower_components/jquery/dist/', expand: true},
                        {
                            dest: "<%= targetdir%>/lib/",
                            src: ["underscore.min.js"],
                            cwd: 'bower_components/underscore/',
                            expand: true
                        },
                        {
                            dest: "<%= targetdir%>/lib/css",
                            src: ["normalize.css"],
                            cwd: 'bower_components/normalize-css/',
                            expand: true
                        },
                        {
                            dest: "<%= targetdir%>/lib/css",
                            src: ["nv.d3.min.css"],
                            cwd: 'bower_components/nvd3/build',
                            expand: true
                        },
                        {
                            dest: "<%= targetdir%>/lib/js",
                            src: ["nv.d3.min.js"],
                            cwd: 'bower_components/nvd3/build',
                            expand: true
                        },
                        {dest: "<%= targetdir%>/", src: ["**"], cwd: 'build/', expand: true},
//                        {dest: "<%= targetdir%>/", src: ["**"], cwd: 'lib/', expand: true},
                        {"<%= targetdir%>/": ["img/**", "js/**"]},

                    ]
                }
            },
            jshint: {
                jshintrc: '.jshintrc',
                files: ['js/**']
            },
            jasmine: {
                pivotal: {
                    src: ['js/*.js'],
                    options: {
                        amd: true,
                        verbose: true,
//                        specs: ['./spec/FooSpec.js', './spec/BarSpec.js'],
                        specs: './spec/**/*Spec.js'
//                        helpers: './spec/**/*Helper.js',
                    }
                }
            },
            compass: {
                dist: {                   // Target
                    options: {              // Target options
                        sassDir: 'scss',
                        cssDir: 'build/css'
//                        environment: 'production'
                    }
                }
            },
            watch: {
                options: {
                    dateFormat: function (time) {
                        grunt.log.writeln('The watch finished in ' + time + 'ms at' + (new Date()).toString());
                        grunt.log.writeln('Waiting for more changes...');
                    }
                },
                files: ['<config:lint.files>', 'js/**', "scss/*.scss"],
                tasks: ['jshint', 'compass', 'copy']
            }
        }
    );

// Default task.
    grunt.registerTask('default', ['jshint', 'compass', 'copy']);
    grunt.loadNpmTasks('grunt-contrib-copy');
    grunt.loadNpmTasks('grunt-contrib-watch');

    grunt.loadNpmTasks('grunt-contrib-jasmine');
    grunt.loadNpmTasks('grunt-contrib-jshint');
    grunt.loadNpmTasks('grunt-contrib-compass');
    grunt.loadNpmTasks('grunt-contrib-uglify');
};
