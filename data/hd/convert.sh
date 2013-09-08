set -x
bname=$(basename -- $1 .zip)
echo "processing $1"
mkdir $bname
cd $bname
unzip ../$1
for fn in *.png; do
	convert $fn -resize 25% new-$fn
	mv new-$fn $fn
done
zip -r ../../sd/$bname.zip *.png
cd ..
rm -rf $bname
