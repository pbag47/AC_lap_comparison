from main_flat import main


application = main(
    data_files_path="compressed_data",
    synchronize_with_remote=False,
)
application.run(debug=True)
