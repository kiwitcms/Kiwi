$(() => {
    if ($('#page-testruns-environment').length === 0) {
        return
    }

    const objectId = $('#environment_pk').data('pk')

    propertiesCard(objectId, 'environment', 'Environment.properties', 'Environment.add_property', 'Environment.remove_property')
})
