from rest_framework import serializers
from .models import User, Author, Tag, Comment, Post, Reader, Like, Follow


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "role"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        user = User(username=validated_data["username"],
                   email = validated_data['email'], role=validated_data["role"])
        user.set_password(validated_data["password"])
        user.save()
        if user.role == "author":
            Author.objects.create(user=user)
        else:
            Reader.objects.create(user=user)

        return user


class AuthorSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Author
        fields = ["id", "user"]


class ReaderSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Reader
        fields = ["id", "user"]


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name"]


class PostSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    tags = serializers.ListField(
        child=serializers.CharField(),
        write_only=True
    )
    status = serializers.ChoiceField(choices = Post.STATUS_CHOICES, default='draft')

    class Meta:
        model = Post
        fields = ["id", "title", "author", "content", "tags", "status","created_at", "updated_at"]

    def create(self, validated_data):
        tags_data = validated_data.pop("tags", [])
        post = Post.objects.create(**validated_data)

        for tag_info in tags_data:
            if tag_info.isdigit():
                tag = Tag.objects.get(id=int(tag_info))
            else:
                tag, created = Tag.objects.get_or_create(name=tag_info)
            post.tags.add(tag)

        return post


class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    post = serializers.PrimaryKeyRelatedField(queryset=Post.objects.all())

    class Meta:
        model = Comment
        fields = ["id", "user", "post", "content", "created_at", "updated_at"]


class LikeSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    post = serializers.PrimaryKeyRelatedField(queryset=Post.objects.all())

    class Meta:
        model = Like
        fields = ["id", "user", "post"]


class FollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = ['id', 'reader', 'author']
        read_only_fields = ['id', 'created_at']

    def validate(self, data):
        reader = data['reader']
        author = data['author']
        if Follow.objects.filter(reader=reader, author=author).exists():
            raise serializers.ValidationError("You are already following this author.")
        return data


