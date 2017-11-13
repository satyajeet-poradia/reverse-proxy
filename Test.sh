# Check for dependencies
python -c "import peewee"
if [ "$?" == 0 ]
then 
    echo "Test case Passed: All depenedencies are installed"
else
    echo "Test case Failes: Use 'pip install peewee' to install required depenedencies"
fi

# Check if config file exist
if [ -f ./config.json ]
then
    echo "Test case Passed: Config file found"
else
    echo "Test case Failes: Please include config file"
fi

# Check if port used in port for proxy server is available
# Please edit the port number used by you below
if lsof -Pi :8080 -sTCP:LISTEN -t > /dev/null;
then
    echo "Test case Failed: Port 8080 is currently in use by another application"
else
    echo "Test case Passed: Port 8080 is available to listen"
fi