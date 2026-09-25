"use client";

import { FormEvent, useMemo, useState } from "react";
import { motion } from "framer-motion";
import {
  CheckCircle2,
  FileImage,
  ImagePlus,
  Loader2,
  Pencil,
  Plus,
  RefreshCw,
  Send,
  Trash2,
  XCircle,
} from "lucide-react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

import {
  useAcademicYears,
  useSchoolList,
} from "@/hooks/use-academic-structure";
import {
  ActivityRecord,
  ActivityStatus,
  useActivities,
  useActivityPhotos,
  useAddActivityPhoto,
  useApproveActivity,
  useCreateActivity,
  useDeleteActivityPhoto,
  usePublishActivity,
  useRejectActivity,
  useSubmitActivity,
  useUpdateActivity,
} from "@/hooks/use-activities";

const statuses: ActivityStatus[] = [
  "DRAFT",
  "SUBMITTED",
  "APPROVED",
  "REJECTED",
  "PUBLISHED",
];

const statusVariant = (status: ActivityStatus) => {
  if (status === "PUBLISHED") return "default" as const;
  if (status === "APPROVED") return "secondary" as const;
  if (status === "REJECTED") return "destructive" as const;
  return "outline" as const;
};

const formatDate = (value?: string | null) => {
  if (!value) return "—";
  return new Intl.DateTimeFormat("en-IN", {
    dateStyle: "medium",
  }).format(new Date(value));
};

export default function ActivitiesPage() {
  const [schoolId, setSchoolId] = useState("");
  const [academicYearId, setAcademicYearId] = useState("");
  const [status, setStatus] = useState<ActivityStatus | "">("");
  const [selectedActivityId, setSelectedActivityId] = useState<string | null>(
    null,
  );

  const [title, setTitle] = useState("");
  const [activityType, setActivityType] = useState("");
  const [activityDate, setActivityDate] = useState("");
  const [visibility, setVisibility] = useState<"INTERNAL" | "PUBLIC">(
    "INTERNAL",
  );
  const [description, setDescription] = useState("");

  const [editMode, setEditMode] = useState(false);

  const [photoFileName, setPhotoFileName] = useState("");
  const [photoStoragePath, setPhotoStoragePath] = useState("");
  const [photoMimeType, setPhotoMimeType] = useState("");
  const [photoFileSize, setPhotoFileSize] = useState("");
  const [photoCaption, setPhotoCaption] = useState("");
  const [photoDisplayOrder, setPhotoDisplayOrder] = useState("0");

  const [creating, setCreating] = useState(false);

  const schoolsQuery = useSchoolList();
  const yearsQuery = useAcademicYears();

  const activitiesQuery = useActivities({
    schoolId: schoolId || undefined,
    academicYearId: academicYearId || undefined,
    status: status || undefined,
  });

  const selectedFromList = useMemo<ActivityRecord | null>(() => {
    if (!selectedActivityId) return null;

    return (
      activitiesQuery.data?.find(
        (activity) => activity.id === selectedActivityId,
      ) ?? null
    );
  }, [activitiesQuery.data, selectedActivityId]);

  const photosQuery = useActivityPhotos(selectedActivityId ?? undefined);

  const createActivity = useCreateActivity();
  const updateActivity = useUpdateActivity(selectedActivityId ?? "");
  const submitActivity = useSubmitActivity(selectedActivityId ?? "");
  const approveActivity = useApproveActivity(selectedActivityId ?? "");
  const rejectActivity = useRejectActivity(selectedActivityId ?? "");
  const publishActivity = usePublishActivity(selectedActivityId ?? "");
  const addPhoto = useAddActivityPhoto(selectedActivityId ?? "");
  const deletePhoto = useDeleteActivityPhoto(selectedActivityId ?? "");


  const schools = schoolsQuery.data ?? [];
  const academicYears = yearsQuery.data ?? [];
  const activities = activitiesQuery.data ?? [];
  const photos = photosQuery.data ?? [];

  const selectedActivity = selectedFromList;
  const isPublished = selectedActivity?.status === "PUBLISHED";
  const canEdit =
    selectedActivity?.status === "DRAFT" ||
    selectedActivity?.status === "REJECTED";

  const selectActivity = (activity: ActivityRecord) => {
    setSelectedActivityId(activity.id);
    setTitle(activity.title ?? "");
    setActivityType(activity.activity_type ?? "");
    setActivityDate(
      activity.activity_date ? activity.activity_date.slice(0, 10) : "",
    );
    setVisibility(activity.visibility ?? "INTERNAL");
    setDescription(activity.description ?? "");
    setEditMode(false);
  };
  const resetCreateForm = () => {
    setTitle("");
    setActivityType("");
    setActivityDate("");
    setVisibility("INTERNAL");
    setDescription("");
  };

  const handleCreate = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!schoolId || !academicYearId) {
      toast.error("Select a school and academic year first.");
      return;
    }

    if (!title.trim() || !activityType.trim() || !activityDate) {
      toast.error("Title, activity type and date are required.");
      return;
    }

    setCreating(true);

    try {
      const created = await createActivity.mutateAsync({
        school_id: schoolId,
        academic_year_id: academicYearId,
        title: title.trim(),
        description: description.trim() || null,
        activity_date: activityDate,
        activity_type: activityType.trim(),
        visibility,
      });

      setSelectedActivityId(created.id);
      resetCreateForm();
      toast.success("Activity created as draft.");
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Unable to create activity.",
      );
    } finally {
      setCreating(false);
    }
  };

  const handleSaveEdit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!selectedActivity || !canEdit) return;

    try {
      await updateActivity.mutateAsync({
        title: title.trim(),
        description: description.trim() || null,
        activity_date: activityDate,
        activity_type: activityType.trim(),
        visibility,
      });

      setEditMode(false);
      toast.success(
        selectedActivity.status === "REJECTED"
          ? "Activity updated and returned to draft."
          : "Activity updated.",
      );
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Unable to update activity.",
      );
    }
  };

  const handleSubmit = async () => {
    if (!selectedActivity) return;

    try {
      await submitActivity.mutateAsync();
      toast.success("Activity submitted for review.");
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Unable to submit activity.",
      );
    }
  };

  const handleApprove = async () => {
    if (!selectedActivity) return;

    try {
      await approveActivity.mutateAsync();
      toast.success("Activity approved.");
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Unable to approve activity.",
      );
    }
  };

  const handleReject = async () => {
    if (!selectedActivity) return;

    const reason = window.prompt("Enter rejection reason:");

    if (!reason?.trim()) {
      toast.error("A rejection reason is required.");
      return;
    }

    try {
      await rejectActivity.mutateAsync(reason.trim());
      toast.success("Activity rejected.");
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Unable to reject activity.",
      );
    }
  };

  const handlePublish = async () => {
    if (!selectedActivity) return;

    try {
      await publishActivity.mutateAsync();
      toast.success("Activity published.");
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Unable to publish activity.",
      );
    }
  };

  const handleAddPhoto = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!selectedActivity || isPublished) return;

    if (!photoFileName.trim() || !photoStoragePath.trim()) {
      toast.error("File name and storage path are required.");
      return;
    }

    try {
      await addPhoto.mutateAsync({
        file_name: photoFileName.trim(),
        storage_path: photoStoragePath.trim(),
        mime_type: photoMimeType.trim(),
        file_size: photoFileSize ? Number(photoFileSize) : 0,
        caption: photoCaption.trim() || null,
        display_order: Number(photoDisplayOrder) || 0,
      });

      setPhotoFileName("");
      setPhotoStoragePath("");
      setPhotoMimeType("");
      setPhotoFileSize("");
      setPhotoCaption("");
      setPhotoDisplayOrder("0");

      toast.success("Media reference added.");
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Unable to add media.",
      );
    }
  };

  const handleDeletePhoto = async (photoId: string) => {
    if (!selectedActivity || isPublished) return;

    try {
      await deletePhoto.mutateAsync(photoId);

      toast.success("Media removed.");
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Unable to remove media.",
      );
    }
  };

  const busy =
    updateActivity.isPending ||
    submitActivity.isPending ||
    approveActivity.isPending ||
    rejectActivity.isPending ||
    publishActivity.isPending ||
    addPhoto.isPending ||
    deletePhoto.isPending;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="text-sm font-medium text-muted-foreground">
            Content management
          </p>
          <h1 className="text-3xl font-semibold tracking-tight">Activities</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Create, review, publish and manage school activities.
          </p>
        </div>

        <Button
          variant="outline"
          onClick={() => activitiesQuery.refetch()}
          disabled={activitiesQuery.isFetching}
        >
          {activitiesQuery.isFetching ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <RefreshCw className="mr-2 h-4 w-4" />
          )}
          Refresh
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Activity filters</CardTitle>
          <CardDescription>
            Narrow the workspace by school, academic year and lifecycle state.
          </CardDescription>
        </CardHeader>

        <CardContent className="grid gap-4 md:grid-cols-3">
          <div className="space-y-2">
            <Label>School</Label>
            <select
              value={schoolId}
              onChange={(event) => {
                setSchoolId(event.target.value);
                setAcademicYearId("");
                setSelectedActivityId(null);
              }}
              className="h-10 w-full rounded-md border bg-background px-3 text-sm"
            >
              <option value="">All schools</option>
              {schools.map((school) => (
                <option key={school.id} value={school.id}>
                  {school.name}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-2">
            <Label>Academic year</Label>
            <select
              value={academicYearId}
              onChange={(event) => {
                setAcademicYearId(event.target.value);
                setSelectedActivityId(null);
              }}
              className="h-10 w-full rounded-md border bg-background px-3 text-sm"
            >
              <option value="">All academic years</option>
              {academicYears.map((year) => (
                <option key={year.id} value={year.id}>
                  {year.name}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-2">
            <Label>Status</Label>
            <select
              value={status}
              onChange={(event) => {
                setStatus(event.target.value as ActivityStatus | "");
                setSelectedActivityId(null);
              }}
              className="h-10 w-full rounded-md border bg-background px-3 text-sm"
            >
              <option value="">All statuses</option>
              {statuses.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-6 xl:grid-cols-[360px_minmax(0,1fr)]">
        <Card className="h-fit">
          <CardHeader>
            <CardTitle>Activities</CardTitle>
            <CardDescription>
              {activities.length} record{activities.length === 1 ? "" : "s"}
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-2">
            {activitiesQuery.isLoading ? (
              <div className="flex items-center justify-center py-10 text-muted-foreground">
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Loading activities...
              </div>
            ) : activities.length === 0 ? (
              <div className="rounded-lg border border-dashed p-6 text-center text-sm text-muted-foreground">
                No activities found for the selected filters.
              </div>
            ) : (
              activities.map((activity) => (
                <button
                  key={activity.id}
                  type="button"
                  onClick={() => selectActivity(activity)}
                  className={`w-full rounded-lg border p-3 text-left transition ${
                    selectedActivityId === activity.id
                      ? "border-primary bg-primary/5"
                      : "hover:bg-muted/50"
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <p className="truncate font-medium">{activity.title}</p>
                      <p className="mt-1 text-xs text-muted-foreground">
                        {formatDate(activity.activity_date)}
                      </p>
                    </div>

                    <Badge variant={statusVariant(activity.status)}>
                      {activity.status}
                    </Badge>
                  </div>
                </button>
              ))
            )}
          </CardContent>
        </Card>

        <div className="space-y-6">
          {!selectedActivity ? (
            <Card>
              <CardHeader>
                <CardTitle>Create activity</CardTitle>
                <CardDescription>
                  New activities start as drafts and can then enter the review
                  workflow.
                </CardDescription>
              </CardHeader>

              <CardContent>
                <form onSubmit={handleCreate} className="space-y-5">
                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="space-y-2">
                      <Label htmlFor="create-title">Title</Label>
                      <Input
                        id="create-title"
                        value={title}
                        onChange={(event) => setTitle(event.target.value)}
                        placeholder="Annual sports day"
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="create-type">Activity type</Label>
                      <Input
                        id="create-type"
                        value={activityType}
                        onChange={(event) =>
                          setActivityType(event.target.value)
                        }
                        placeholder="Sports"
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="create-date">Activity date</Label>
                      <Input
                        id="create-date"
                        type="date"
                        value={activityDate}
                        onChange={(event) =>
                          setActivityDate(event.target.value)
                        }
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="create-visibility">Visibility</Label>
                      <select
                        id="create-visibility"
                        value={visibility}
                        onChange={(event) =>
                          setVisibility(
                            event.target.value as "INTERNAL" | "PUBLIC",
                          )
                        }
                        className="h-10 w-full rounded-md border bg-background px-3 text-sm"
                      >
                        <option value="INTERNAL">Internal</option>
                        <option value="PUBLIC">Public</option>
                      </select>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="create-description">Description</Label>
                    <Textarea
                      id="create-description"
                      value={description}
                      onChange={(event) => setDescription(event.target.value)}
                      placeholder="Describe the activity..."
                      rows={5}
                    />
                  </div>

                  <Button type="submit" disabled={creating}>
                    {creating ? (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                      <Plus className="mr-2 h-4 w-4" />
                    )}
                    Create draft
                  </Button>
                </form>
              </CardContent>
            </Card>
          ) : (
            <motion.div
              key={selectedActivity.id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-6"
            >
              <Card>
                <CardHeader>
                  <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <CardTitle>{selectedActivity.title}</CardTitle>
                        <Badge
                          variant={statusVariant(selectedActivity.status)}
                        >
                          {selectedActivity.status}
                        </Badge>
                      </div>

                      <CardDescription className="mt-2">
                        {selectedActivity.activity_type} ·{" "}
                        {formatDate(selectedActivity.activity_date)} ·{" "}
                        {selectedActivity.visibility}
                      </CardDescription>
                    </div>

                    <div className="flex flex-wrap gap-2">
                      {canEdit && !editMode && (
                        <Button
                          variant="outline"
                          onClick={() => setEditMode(true)}
                        >
                          <Pencil className="mr-2 h-4 w-4" />
                          Edit
                        </Button>
                      )}

                      {canEdit && (
                        <Button onClick={handleSubmit} disabled={busy}>
                          {submitActivity.isPending ? (
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          ) : (
                            <Send className="mr-2 h-4 w-4" />
                          )}
                          Submit
                        </Button>
                      )}

                      {selectedActivity.status === "SUBMITTED" && (
                        <>
                          <Button
                            variant="outline"
                            onClick={handleReject}
                            disabled={busy}
                          >
                            {rejectActivity.isPending ? (
                              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            ) : (
                              <XCircle className="mr-2 h-4 w-4" />
                            )}
                            Reject
                          </Button>

                          <Button onClick={handleApprove} disabled={busy}>
                            {approveActivity.isPending ? (
                              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            ) : (
                              <CheckCircle2 className="mr-2 h-4 w-4" />
                            )}
                            Approve
                          </Button>
                        </>
                      )}

                      {selectedActivity.status === "APPROVED" && (
                        <Button onClick={handlePublish} disabled={busy}>
                          {publishActivity.isPending ? (
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          ) : (
                            <Send className="mr-2 h-4 w-4" />
                          )}
                          Publish
                        </Button>
                      )}
                    </div>
                  </div>
                </CardHeader>

                <CardContent>
                  {editMode && canEdit ? (
                    <form onSubmit={handleSaveEdit} className="space-y-5">
                      <div className="grid gap-4 md:grid-cols-2">
                        <div className="space-y-2">
                          <Label htmlFor="edit-title">Title</Label>
                          <Input
                            id="edit-title"
                            value={title}
                            onChange={(event) => setTitle(event.target.value)}
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="edit-type">Activity type</Label>
                          <Input
                            id="edit-type"
                            value={activityType}
                            onChange={(event) =>
                              setActivityType(event.target.value)
                            }
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="edit-date">Activity date</Label>
                          <Input
                            id="edit-date"
                            type="date"
                            value={activityDate}
                            onChange={(event) =>
                              setActivityDate(event.target.value)
                            }
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="edit-visibility">Visibility</Label>
                          <select
                            id="edit-visibility"
                            value={visibility}
                            onChange={(event) =>
                              setVisibility(
                                event.target.value as "INTERNAL" | "PUBLIC",
                              )
                            }
                            className="h-10 w-full rounded-md border bg-background px-3 text-sm"
                          >
                            <option value="INTERNAL">Internal</option>
                            <option value="PUBLIC">Public</option>
                          </select>
                        </div>
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="edit-description">Description</Label>
                        <Textarea
                          id="edit-description"
                          value={description}
                          onChange={(event) =>
                            setDescription(event.target.value)
                          }
                          rows={6}
                        />
                      </div>

                      <div className="flex gap-2">
                        <Button type="submit" disabled={updateActivity.isPending}>
                          {updateActivity.isPending ? (
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          ) : (
                            <CheckCircle2 className="mr-2 h-4 w-4" />
                          )}
                          Save changes
                        </Button>

                        <Button
                          type="button"
                          variant="ghost"
                          onClick={() => setEditMode(false)}
                          disabled={updateActivity.isPending}
                        >
                          Cancel
                        </Button>
                      </div>
                    </form>
                  ) : (
                    <div className="space-y-4">
                      <div className="rounded-lg bg-muted/40 p-4">
                        <p className="whitespace-pre-wrap text-sm leading-6">
                          {selectedActivity.description || "No description."}
                        </p>
                      </div>

                      {selectedActivity.status === "REJECTED" &&
                        selectedActivity.rejection_reason && (
                          <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-4">
                            <p className="text-sm font-medium">
                              Rejection reason
                            </p>
                            <p className="mt-1 text-sm text-muted-foreground">
                              {selectedActivity.rejection_reason}
                            </p>
                          </div>
                        )}

                      {isPublished && (
                        <div className="rounded-lg border bg-muted/30 p-4 text-sm text-muted-foreground">
                          This activity is published and is now read-only.
                        </div>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <FileImage className="h-5 w-5" />
                    Media
                  </CardTitle>
                  <CardDescription>
                    Manage image/media references attached to this activity.
                  </CardDescription>
                </CardHeader>

                <CardContent className="space-y-6">
                  {!isPublished && (
                    <form
                      onSubmit={handleAddPhoto}
                      className="rounded-xl border bg-muted/20 p-4"
                    >
                      <div className="mb-4 flex items-center gap-2">
                        <ImagePlus className="h-4 w-4" />
                        <p className="font-medium">Add media reference</p>
                      </div>

                      <div className="grid gap-4 md:grid-cols-2">
                        <div className="space-y-2">
                          <Label htmlFor="photo-file-name">File name</Label>
                          <Input
                            id="photo-file-name"
                            value={photoFileName}
                            onChange={(event) =>
                              setPhotoFileName(event.target.value)
                            }
                            placeholder="sports-day-01.jpg"
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="photo-storage-path">
                            Storage path
                          </Label>
                          <Input
                            id="photo-storage-path"
                            value={photoStoragePath}
                            onChange={(event) =>
                              setPhotoStoragePath(event.target.value)
                            }
                            placeholder="activities/2026/sports-day-01.jpg"
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="photo-mime-type">MIME type</Label>
                          <Input
                            id="photo-mime-type"
                            value={photoMimeType}
                            onChange={(event) =>
                              setPhotoMimeType(event.target.value)
                            }
                            placeholder="image/jpeg"
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="photo-size">File size</Label>
                          <Input
                            id="photo-size"
                            type="number"
                            min="0"
                            value={photoFileSize}
                            onChange={(event) =>
                              setPhotoFileSize(event.target.value)
                            }
                            placeholder="245760"
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="photo-caption">Caption</Label>
                          <Input
                            id="photo-caption"
                            value={photoCaption}
                            onChange={(event) =>
                              setPhotoCaption(event.target.value)
                            }
                            placeholder="Students participating in sports day"
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="photo-order">Display order</Label>
                          <Input
                            id="photo-order"
                            type="number"
                            min="0"
                            value={photoDisplayOrder}
                            onChange={(event) =>
                              setPhotoDisplayOrder(event.target.value)
                            }
                          />
                        </div>
                      </div>

                      <Button
                        type="submit"
                        className="mt-4"
                        disabled={addPhoto.isPending}
                      >
                        {addPhoto.isPending ? (
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        ) : (
                          <Plus className="mr-2 h-4 w-4" />
                        )}
                        Add media
                      </Button>
                    </form>
                  )}

                  {isPublished && (
                    <div className="rounded-lg border bg-muted/30 p-4 text-sm text-muted-foreground">
                      Published activity media is read-only.
                    </div>
                  )}

                  {photosQuery.isLoading ? (
                    <div className="flex items-center justify-center py-8 text-muted-foreground">
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Loading media...
                    </div>
                  ) : photos.length === 0 ? (
                    <div className="rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground">
                      No media attached yet.
                    </div>
                  ) : (
                    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                      {photos.map((photo) => (
                        <div
                          key={photo.id}
                          className="overflow-hidden rounded-xl border"
                        >
                          <div className="flex h-36 items-center justify-center bg-muted">
                            <FileImage className="h-10 w-10 text-muted-foreground" />
                          </div>

                          <div className="space-y-3 p-4">
                            <div>
                              <p className="truncate font-medium">
                                {photo.file_name}
                              </p>
                              <p className="mt-1 truncate text-xs text-muted-foreground">
                                {photo.storage_path}
                              </p>
                            </div>

                            {photo.caption && (
                              <p className="text-sm text-muted-foreground">
                                {photo.caption}
                              </p>
                            )}

                            {!isPublished && (
                              <Button
                                variant="outline"
                                size="sm"
                                className="w-full"
                                onClick={() => handleDeletePhoto(photo.id)}
                                disabled={deletePhoto.isPending}
                              >
                                {deletePhoto.isPending ? (
                                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                ) : (
                                  <Trash2 className="mr-2 h-4 w-4" />
                                )}
                                Remove
                              </Button>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
}




