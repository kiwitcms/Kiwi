import { propertiesCard } from '../../../../static/js/properties'

export function pageTestrunsEnvironmentReadyHandler () {
    const objectId = $('#environment_pk').data('pk')

    propertiesCard(objectId, 'environment', 'Environment.properties', 'Environment.add_property', 'Environment.remove_property')
}
