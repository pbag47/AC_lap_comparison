from main_flat import main


application = main(
    data_files_path="processed_data",
    synchronize_with_remote=True,
)
application.run(debug=True)
