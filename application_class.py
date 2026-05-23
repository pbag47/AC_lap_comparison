from main_local import main
import logging

logging.basicConfig(
    filename='logs/main_prod_v0.log',
    level=logging.INFO,
)
application = main(
    data_files_path="processed_data",
)
server = application.server
application.run(debug=True)
