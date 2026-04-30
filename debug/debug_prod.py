from debug_local import main


application = main()
server = application.server
application.run(debug=True)

