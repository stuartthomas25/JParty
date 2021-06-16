import sys
from jparty.welcome_window import main


if __name__ == '__main__':
    f = open('/Users/Stuart/jparty_out.log', 'w')
    sys.stdout = f
    sys.stderr = f
    main()
