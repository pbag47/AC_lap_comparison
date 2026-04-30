from main_local import main


application = main(
    data_files_path="processed_data",
    synchronize_with_remote=True,
)
server = application.server
application.run(debug=True)
