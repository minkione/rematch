from rest_framework import serializers
from collab.models import (Project, File, FileVersion, Task, Instance, Vector,
                           Annotation, Match)


class ProjectSerializer(serializers.ModelSerializer):
  owner = serializers.ReadOnlyField(source='owner.username')
  created = serializers.ReadOnlyField()

  class Meta:
    model = Project
    fields = ('id', 'created', 'owner', 'name', 'description', 'private',
              'files')


class FileSerializer(serializers.ModelSerializer):
  owner = serializers.ReadOnlyField(source='owner.username')
  created = serializers.ReadOnlyField()

  class Meta:
    model = File
    fields = ('id', 'created', 'owner', 'project', 'name', 'description',
              'md5hash', 'file')


class FileVersionSerializer(serializers.ModelSerializer):
  class Meta:
    model = FileVersion
    fields = ('id', 'created', 'file', 'md5hash')


class TaskSerializer(serializers.ModelSerializer):
  owner = serializers.ReadOnlyField(source='owner.username')
  source_file = serializers.ReadOnlyField(source='source_file_version.file_id')
  task_id = serializers.ReadOnlyField()
  created = serializers.ReadOnlyField()
  finished = serializers.ReadOnlyField()
  status = serializers.ReadOnlyField()
  progress = serializers.ReadOnlyField()
  progress_max = serializers.ReadOnlyField()

  class Meta:
    model = Task
    fields = ('id', 'task_id', 'created', 'finished', 'owner', 'status',
              'target_project', 'target_file', 'source_file',
              'source_file_version', 'source_start', 'source_end', 'progress',
              'progress_max')


class TaskEditSerializer(TaskSerializer):
  target_project = serializers.ReadOnlyField()
  target_file = serializers.ReadOnlyField()
  source_file = serializers.ReadOnlyField()
  source_file_version = serializers.ReadOnlyField()
  source_start = serializers.ReadOnlyField()
  source_end = serializers.ReadOnlyField()


class TaskInstanceSerializer(serializers.ModelSerializer):
  class NestedMatchSerializer(serializers.ModelSerializer):
    class Meta:
      model = Match
      fields = ('to_instance', 'type', 'score')

  matches = serializers.SerializerMethodField()

  class Meta:
    model = Instance
    fields = ('id', 'type', 'offset', 'matches')

  def __init__(self, task_id, *args, **kwargs):
    super(TaskInstanceSerializer, self).__init__(*args, **kwargs)
    self.task_id = task_id

  def get_matches(self, instance):
    matches = Match.objects.filter(from_instance=instance,
                                   task_id=self.task_id)
    serializer = self.NestedMatchSerializer(matches, many=True)
    return serializer.data


class SimpleInstanceSerializer(serializers.ModelSerializer):
  class Meta:
    model = Instance
    fields = ('id', 'file_version', 'type', 'offset')


class InstanceSerializer(serializers.ModelSerializer):
  owner = serializers.ReadOnlyField(source='owner.username')
  file = serializers.ReadOnlyField(source='file_version.file_id')

  class Meta:
    model = Instance
    fields = ('id', 'owner', 'file', 'file_version', 'type', 'offset',
              'vectors', 'annotations')


class InstanceVectorSerializer(InstanceSerializer):
  class NestedVectorSerializer(serializers.ModelSerializer):
    class Meta:
      model = Vector
      fields = ('id', 'type', 'type_version', 'data')

  class NestedAnnotationSerializer(serializers.ModelSerializer):
    class Meta:
      model = Annotation
      fields = ('id', 'type', 'data')

  vectors = NestedVectorSerializer(many=True, required=True)
  annotations = NestedAnnotationSerializer(many=True, required=True)

  def create(self, validated_data):
    vectors_data = validated_data.pop('vectors')
    annotations_data = validated_data.pop('annotations')
    file_version = validated_data['file_version']

    obj = self.Meta.model.objects.create(**validated_data)
    vectors = (Vector(instance=obj, file_version=file_version,
                      file=file_version.file, **vector_data)
               for vector_data in vectors_data)
    Vector.objects.bulk_create(vectors)
    annotations = (Annotation(instance=obj, **annotation_data)
                   for annotation_data in annotations_data)
    Annotation.objects.bulk_create(annotations)
    return obj


class VectorSerializer(serializers.ModelSerializer):
  file = serializers.ReadOnlyField(source='file_version.file_id')

  class Meta:
    model = Vector
    fields = ('id', 'file', 'file_version', 'instance', 'type', 'type_version',
              'data')

  def create(self, validated_data):
    file = validated_data['file_version'].file
    return self.Meta.model.objects.create(file=file, **validated_data)


class MatchSerializer(serializers.ModelSerializer):
  class Meta:
    model = Match
    fields = ('from_vector', 'to_vector', 'from_instance', 'to_instance',
              'task', 'type', 'score')
