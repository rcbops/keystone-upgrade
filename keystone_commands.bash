#!/bin/bash

#      type       : role, tenant, user, token, endpoint, endpointTemplates
#      command    : add, list, disable, delete, grant, revoke

CMD='keystone-manage'
VERSION=`dpkg -l | grep keystone | head -1 | awk '{print $3}' | cut -d '-' -f1,2`

echo "***** TENANT LIST ****"
${CMD} tenant list
if [ $VERSION == '2011.3-d5' ]; then
    tenants=(`${CMD} tenant list | grep -v -e 'enabled$' -e '^--' | awk '{print $1}'`)
else
    # currently works for 2011.3-final
    tenants=(`${CMD} tenant list | grep -v -e 'enabled$' -e '^--' | awk '{print $2}'`)
fi
# for i in $(seq 0 $((${#tenants[@]} - 1))); do echo ${tenants[i]}; done
echo ""

echo "***** USER LIST ****"
${CMD} user list
users=(`${CMD} user list | grep -v -e '^id' -e '^--' | awk '{print $2}'`)
# for i in $(seq 0 $((${#users[@]} - 1))); do echo ${users[i]}; done
echo ""

echo "***** ROLE LIST ****"
${CMD} role list
echo ""

for i in $(seq 0 $((${#tenants[@]} - 1))); do
  echo "    ** ROLE LIST - TENANT ${tenants[i]} **"
  ${CMD} role list ${tenants[i]}; 
  echo ""
done
echo ""

echo "***** SERVICE LIST ****"
${CMD} service list
echo ""

echo "***** ENDPOINT_TEMPLATES LIST ****"
${CMD} endpointTemplates list
echo ""

echo "***** TOKEN LIST *****"
${CMD} token list
echo ""

echo "***** ENDPOINT LIST *****"
${CMD} endpoint list
echo "FUNCTION DOES NOT EXIST IN KEYSTONE"
echo ""

echo "***** CREDENTIALS LIST *****"
${CMD} credentials list
echo ""
