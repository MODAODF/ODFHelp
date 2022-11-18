ZIP=`which zip`
Productname=ODFHelp

all:
	./addver.sh; \
	cd src; \
	$(ZIP) -r ../$(Productname).oxt *; \
	cd -; \
	echo -e "\nbuild $(Productname) success..."
