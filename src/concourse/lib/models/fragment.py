from pydantic import BaseModel, Field, validator

from concourse.lib.models.pipeline import Job, Resource, ResourceType


class PipelineFragment(BaseModel):
    resource_types: list[ResourceType] = Field(default_factory=list)
    resources: list[Resource] = Field(default_factory=list)
    jobs: list[Job] = Field(default_factory=list)

    @validator("resource_types")
    def deduplicate_resource_types(
        cls: "PipelineFragment", resource_types: list[ResourceType]
    ):
        """Ensure that there are no duplicate resource type definitions.

        Concourse pipelines don't support duplicate definitions of resource types, where
        the `name` identifier is used to determine uniqueness.  This ensurs that
        `PipelineFragment` objects can be composed together without violating that
        requirement.

        :param cls: The class object
        :param resource_types: The list of resource types defined in the class instance.

        :returns: A list of resource types that have been deduplicated
        """
        unique_resource_types = []
        resource_type_identifiers = set()
        for resource_type in resource_types or []:
            if resource_type.name not in resource_type_identifiers:
                resource_type_identifiers.add(resource_type.name)
                unique_resource_types.append(resource_type)
        return unique_resource_types

    @validator("resources")
    def deduplicate_resources(cls: "PipelineFragment", resources: list[Resource]):
        """Ensure that there are no duplicate resource definitions.

        Concourse pipelines don't support duplicate definitions of resources, where
        the `name` identifier is used to determine uniqueness.  This ensurs that
        `PipelineFragment` objects can be composed together without violating that
        requirement.

        :param cls: The class object
        :param resources: The list of resources defined on the class instance
        :returns: A list of resources that has been deduplicated.

        """
        unique_resources = []
        resource_identifiers = set()
        for resource in resources or []:
            if resource.name not in resource_identifiers:
                resource_identifiers.add(resource.name)
                unique_resources.append(resource)
        return unique_resources
