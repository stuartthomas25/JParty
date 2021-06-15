import sys
from jparty.welcome_window import main


if __name__ == '__main__':
    print("THIS MUST BE RUN FROM THE 'jparty' DIRECTORY")
    f = open('/Users/Stuart/jparty_out.log', 'w')
    sys.stdout = f
    sys.stderr = f
    main()
