#gcloud auth login --update-adc
#docker buildx build --platform linux/amd64 -t europe-west1-docker.pkg.dev/remote-observatory-dev-jcy/remote-observatory-main-repo/remote_observatory:latest .
#docker push europe-west1-docker.pkg.dev/remote-observatory-dev-jcy/remote-observatory-main-repo/remote_observatory:latest
rm -rf ./ubuntu.*
packer build -var-file=./vars/ubuntu.pkrvars.hcl -only="gen-fs-tarball.*" ./templates/ubuntu-template.pkr.hcl
mkdir -p ./ubuntu.dir
tar -vxf ubuntu.tar -C ubuntu.dir
packer build -var-file=./vars/ubuntu.pkrvars.hcl -only="gen-boot-img.*" ./templates/ubuntu-template.pkr.hcl
packer build -var-file=./vars/ubuntu.pkrvars.hcl -only="customize-boot-img.*" ./templates/ubuntu-template.pkr.hcl
gunzip -f ./customized_ubuntu.img.gz
