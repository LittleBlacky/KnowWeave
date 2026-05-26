"use client";

import { Plus, Tag as TagIcon } from "lucide-react";
import { useEffect, useState } from "react";

import { createTag, listTags, type Tag } from "@/shared/api/knowweave";

export function TagManager() {
  const [tags, setTags] = useState<Tag[]>([]);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [color, setColor] = useState("#2563eb");

  useEffect(() => {
    async function loadTags() {
      const response = await listTags();
      setTags(response.items);
    }
    void loadTags();
  }, []);

  async function handleCreate() {
    if (!name.trim()) {
      return;
    }
    const created = await createTag({
      name: name.trim(),
      description: description.trim() || undefined,
      color,
    });
    setTags((current) => [created, ...current]);
    setName("");
    setDescription("");
  }

  return (
    <section className="rounded-md border border-[#dcded8] bg-white">
      <div className="flex items-center justify-between border-b border-[#dcded8] px-4 py-3">
        <h2 className="text-base font-semibold">Tags</h2>
        <TagIcon aria-hidden="true" className="text-[#275a53]" size={18} />
      </div>
      <div className="grid gap-4 p-4">
        <div className="grid grid-cols-[minmax(0,0.8fr)_minmax(0,1fr)_120px_auto] gap-2 max-lg:grid-cols-1">
          <label className="grid gap-2 text-sm font-semibold">
            Tag name
            <input
              className="rounded-md border border-[#dcded8] px-3 py-2 font-normal"
              onChange={(event) => setName(event.target.value)}
              value={name}
            />
          </label>
          <label className="grid gap-2 text-sm font-semibold">
            Tag description
            <input
              className="rounded-md border border-[#dcded8] px-3 py-2 font-normal"
              onChange={(event) => setDescription(event.target.value)}
              value={description}
            />
          </label>
          <label className="grid gap-2 text-sm font-semibold">
            Color
            <input
              className="h-10 rounded-md border border-[#dcded8] px-2"
              onChange={(event) => setColor(event.target.value)}
              type="color"
              value={color}
            />
          </label>
          <button
            className="inline-flex items-center justify-center gap-2 self-end rounded-md bg-[#123d37] px-3 py-2 text-sm font-semibold text-white"
            onClick={() => void handleCreate()}
            type="button"
          >
            <Plus aria-hidden="true" size={16} />
            Create tag
          </button>
        </div>

        <div className="grid gap-2">
          {tags.map((tag) => (
            <div
              className="flex items-center justify-between gap-3 rounded-md border border-[#dcded8] p-3"
              key={tag.id}
            >
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <span
                    aria-hidden="true"
                    className="size-3 rounded-full"
                    style={{ backgroundColor: tag.color ?? "#275a53" }}
                  />
                  <h3 className="font-semibold">{tag.name}</h3>
                </div>
                {tag.description ? (
                  <p className="mt-1 text-sm text-[#5d645d]">{tag.description}</p>
                ) : null}
              </div>
              <span className="shrink-0 rounded-md border border-[#dcded8] px-2 py-1 text-xs">
                {tag.binding_count ?? 0} {(tag.binding_count ?? 0) === 1 ? "binding" : "bindings"}
              </span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
