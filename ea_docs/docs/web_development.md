# HTML/JS/D3 Development


## Overview
First visit the [admin console](http://localhost:8000/admin/) console to login.

Now visit [http://localhost:8000/device/1](http://localhost:8000/device/1) to see a device detail view that uses the API.

Let us look at the url definition file `ep/urls/api`.
This catches the pattern `url(r'^device/(?P<device_parameter_id>[0-9]+)$'`
which calls `MeasurementList` and is accessible in the templates by name `api:device_measurements`.

Pro tip: Find out how you can use keyboard shortcuts to navigate from the api urls definition directly to the definition of the view.
(F3 on my layout "Eclipse" - bring up the settings, keymap and search for navigate declaration to find out).

This view returns measurement data as JSON via the URL `/api/device/(?P<device_parameter_id>[0-9]+)`.

## Handling JS Dependencies
It is advised to use bower to manage JS dependencies. 

For that you need grunt and bower. You can run both through ... docker, yay! So cool!

**replace your user name**
### 1. Build the NPM image
run `docker build -t npmbuilder -f deployment/NPMDockerfile docker` to build the image.
### 2. Log on
Then run `docker run -v /c/user/expsb/ep_site:/app -w /app/ep -ti npmbuilder bash` to log on.

### 2.b) Or run commands directly
Run `docker run -v /c/user/expsb/ep_site:/app -w /app/ep -ti npmbuilder <command>`.

### 3. Install dependencies
Run `docker run -v /c/user/expsb/ep_site:/app -w /app/ep -ti npmbuilder bower install` to install all dependencies 
into the `bower_components` directory.
Also run `npm install --dev` to install the grunt dev dependencies. 


### 4. Example workflow
Before you test changes you made to `JS`, `CSS` or `HTML` files run 
`docker run -v /c/user/<jadajada>/ep_site:/app -w /app/ep -ti npmbuilder grunt copy` to copy those files to where you can
reference them in your templates - this is the `../static` directory in the project root. 
`Grunt copy` finds this setting defined in the variable `<%= targetdir%>` in the `Gruntfile` in the ep directory.

If you have additional dependencies, you can install these by running `bower install <name>`.
Then add a section to the copy fragment in the `Gruntfile`. 
It is pretty self evident.
`{dest: "<%= targetdir%>/lib/", src: ["**"], cwd: 'bower_components/jquery/dist/', expand: true},` copies all files from
 `bower_components/jquery/dist/` to the targetdir `lib` folder.
  
