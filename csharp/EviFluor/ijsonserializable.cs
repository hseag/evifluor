using System.Text.Json.Nodes;

/// <summary>
/// Defines a contract for types that can serialize themselves to a <see cref="System.Text.Json.Nodes.JsonNode"/>.
/// </summary>
public interface IJsonSerializable
{
    /// <summary>
    /// Converts the current instance to a JSON-serializable <see cref="JsonNode"/> structure.
    /// </summary>
    /// <returns>A <see cref="JsonNode"/> that represents the current object.</returns>
    JsonNode ToJson();
}