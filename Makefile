ZIP=`which zip`
Productname=NDCHelp


all:
	cd src; \
	${ZIP} -r ../${Productname}.oxt *; \
	cd -; \
	echo -e "\nbuild ${Productname} success..."
