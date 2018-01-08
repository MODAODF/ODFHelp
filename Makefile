ZIP=`which zip`
Productname=NDCHelp

all:
	./addver.sh \
	cd src; \
	$(ZIP) -r ../$(Productname).oxt *; \
	cd -; \
	echo -e "\nbuild $(Productname) success..."
