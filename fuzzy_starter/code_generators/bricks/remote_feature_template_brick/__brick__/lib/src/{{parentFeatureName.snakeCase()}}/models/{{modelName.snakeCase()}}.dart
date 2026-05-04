class {{modelName.pascalCase()}} {
  final String appSpecificParameter;

  {{modelName.pascalCase()}}({
    this.appSpecificParameter = '',
  });

  Map<String, dynamic> toMap() {
    return <String, dynamic>{
      'appSpecificParameter': appSpecificParameter,
    };
  }

  factory {{modelName.pascalCase()}}.fromMap(Map<String, dynamic> map) {
    return {{modelName.pascalCase()}}(
      appSpecificParameter: map['appSpecificParameter'] as String,
    );
  }
}
